###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
This package contains the interface to AutoAuto v1 microcontroller which we
communicate with via I2C from this host.
"""


"""
In my tests, it seems that the I2C bus will fail ~1/200 times. We can
detect those failures with high probability due to our integrity checks
which we use for all I2C messages, so that's good. Furthermore, we have
a method for automatically retrying failed I2C transactions! In fact, if
we take the 1/200 failure rate as a given, then by retrying up to 5 times
(total, meaning 1 attempt and 4 retries) and assuming independence, we
conclude that we will only see a failure:
    (1/200)**5 = 1/320000000000
Thus, if we do 300 transactions per second, we'll see, on average, one
failure every ~34 years. Someone check my math.
"""
N_I2C_TRIES = 10


"""
For this particular controller, we talk to it via I2C.
"""
CONTROLLER_I2C_SLAVE_ADDRESS = 0x14


import asyncio

from . import capabilities
from . import easyi2c

import cio


class CioRoot(cio.CioRoot):
    """
    This is the CIO root interface for the AutoAuto v1.x microcontrollers.
    """

    def __init__(self):
        self.fd = None
        self.caps = None
        self.lock = asyncio.Lock()
        self.capability_ref_count = {}

    async def init(self):
        """
        Attempt to initialize the version 1.x AutoAuto controller. Return a list
        of capabilities if initialization worked, else raise an exception.
        """
        try:
            self.fd = await easyi2c.open_i2c(1, CONTROLLER_I2C_SLAVE_ADDRESS)
            self.caps = await capabilities.get_capabilities(self.fd, soft_reset_first=True)

            if 'VersionInfo' not in self.caps:
                raise Exception('Controller does not implement the required VersionInfo component.')

            version_info = await self.acquire('VersionInfo')
            major, minor = await version_info.version()
            await self.release(version_info)

            if major != 1:
                raise Exception('Controller is not version 1, thus this interface will not work.')

            for component_name, config in self.caps.items():
                if config['is_enabled']:
                    # This component is enabled by default, so make sure it stays enabled!
                    # We'll do this by starting its ref count at 1, so it will never go
                    # to zero -- it's as if the controller itself holds one reference.
                    self.capability_ref_count[component_name] = 1

        except:
            if self.fd is not None:
                await easyi2c.close_i2c(self.fd)
                self.fd = None
            raise

        _setup_cleanup(self.fd)
        return list(self.caps.keys())

    async def acquire(self, capability_id):
        """
        Acquire the interface to the component with the given `capability_id`, and return
        a concrete object implementing its interface.
        """
        async with self.lock:
            return await capabilities.acquire_component_interface(self.fd, self.caps, self.capability_ref_count, capability_id)

    async def release(self, capability_obj):
        """
        Release a previously acquired capability interface. You must pass
        the exact object returned by `acquire()`.
        """
        async with self.lock:
            await capabilities.release_component_interface(self.capability_ref_count, capability_obj)


def _setup_cleanup(fd):
    """
    Try our best to cleanup when this python process exits.
    We clean up by telling the microcontroller to reset itself.
    """
    from . import reset
    import atexit, time, signal

    def cleanup():
        time.sleep(0.1)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        coro = reset.soft_reset(fd)
        if loop is not None:
            loop.run_until_complete(coro)
        else:
            asyncio.run(coro)

    atexit.register(cleanup)

    def handle_sig_hup(signum, frame):
        # By default, the Python process will not handle this signal.
        # Furthermore, Python cannot call the "atexit" routines whenever
        # the process exits due to an unhandled signal. Therefore, by
        # default, our "cleanup" function above would not be called
        # if this process were to receive this signal. This is bad for us
        # because our PTY manager sends this signal whenever the user
        # clicks the "STOP" button on the CDP. All is well and good if
        # we just handle this signal. So we are.
        raise KeyboardInterrupt("STOP button pressed")

    signal.signal(signal.SIGHUP, handle_sig_hup)

