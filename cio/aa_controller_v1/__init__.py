###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
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
from . import reset

import cio

from auto.services.labs.settings import load_settings


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
        async with self.lock:
            if self.fd is not None:
                return

            try:
                self.fd = await easyi2c.open_i2c(1, CONTROLLER_I2C_SLAVE_ADDRESS)
                self.caps = await capabilities.get_capabilities(self.fd, soft_reset_first=True)

                for component_name, config in self.caps.items():
                    if config['is_enabled']:
                        # This component is enabled by default, so make sure it stays enabled!
                        # We'll do this by starting its ref count at 1, so it will never go
                        # to zero -- it's as if the controller itself holds one reference.
                        self.capability_ref_count[component_name] = 1

                if 'VersionInfo' not in self.caps:
                    raise Exception('Controller does not implement the required VersionInfo component.')

                version_info = await capabilities.acquire_component_interface(self.fd, self.caps, self.capability_ref_count, 'VersionInfo')
                major, minor = await version_info.version()
                await capabilities.release_component_interface(self.capability_ref_count, version_info)

                if major != 1:
                    raise Exception('Controller is not version 1, thus this interface will not work.')

                self.caps['Camera'] = {
                    'register_number': None,   # <-- this is a virtual component; it is implemented on the Python side, not the controller side
                    'is_enabled': False
                }

                if 'CarMotors' in self.caps:
                    reg_num_car_motors = self.caps['CarMotors']['register_number']
                    reg_num_gyro_accum = self.caps.get('Gyroscope_accum', {}).get('register_number', None)
                    reg_num_pid_steering = self.caps.get('PID_steering', {}).get('register_number', None)
                    self.caps['CarControl'] = {
                        'register_number': (reg_num_car_motors, reg_num_gyro_accum, reg_num_pid_steering),
                        'is_enabled': False,
                    }

            except:
                if self.fd is not None:
                    await easyi2c.close_i2c(self.fd)
                    self.fd = None
                    self.caps = None
                    self.capability_ref_count = {}
                raise

            settings = load_settings()
            if isinstance(settings, dict) and 'cio' in settings:
                cio_settings = settings['cio']
                if isinstance(cio_settings, dict) and 'disabled' in cio_settings:
                    cio_disabled = cio_settings['disabled']
                    if isinstance(cio_disabled, list):
                        for disabled_component_name in cio_disabled:
                            if disabled_component_name in self.caps:
                                del self.caps[disabled_component_name]

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

    async def close(self):
        """
        Close the connection and reset the controller, thereby invalidating and releasing all acquired components.
        """
        async with self.lock:
            if self.fd is None:
                return

            await reset.soft_reset(self.fd)

            await easyi2c.close_i2c(self.fd)
            self.fd = None
            self.caps = None
            self.capability_ref_count = {}

