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
This package contains the interface to AutoAuto v3 microcontroller which we
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
I2C_BUS_INDEX = 1
CONTROLLER_I2C_SLAVE_ADDRESS = 0x15
BATT_CONTROLLER_SLAVE_ADDRESS = 0x6a


import asyncio

from . import capabilities
from . import easyi2c
from . import reset
from . import imu

from .components import KNOWN_COMPONENTS

import cio

from auto.services.labs.settings import load_settings


class CioRoot(cio.CioRoot):
    """
    This is the CIO root interface for the AutoAuto v3.x microcontrollers.
    """

    def __init__(self):
        self.ctlr_fd = None
        self.caps = None
        self.batt_fd = None
        self.refcounts = {}   # maps `capability_id` to integer refcount
        self.objects = {}     # maps `capability_id` to first object of that type

    async def init(self):
        """
        Attempt to initialize the version 3.x AutoAuto controller. Return a list
        of capabilities if initialization worked, else raise an exception.
        """
        try:
            self.ctlr_fd = await easyi2c.open_i2c(I2C_BUS_INDEX, CONTROLLER_I2C_SLAVE_ADDRESS)
            self.caps = await capabilities.get_capabilities(self.ctlr_fd, soft_reset_first=True)

            version_info = await self.acquire('VersionInfo')
            major, minor = await version_info.version()
            await self.release(version_info)

            if major != 3:
                raise Exception('Controller is not version 3, thus this interface will not work.')

            self.batt_fd = await easyi2c.open_i2c(I2C_BUS_INDEX, BATT_CONTROLLER_SLAVE_ADDRESS)
            self.caps['Power'] = {
                'fd': self.batt_fd,
                'register_number': None,
            }

            imu.start_thread()
            loop = asyncio.get_running_loop()
            imu_start = loop.time()
            imu_working = True
            while imu.DATA is None:
                if loop.time() - imu_start > 1.0:
                    imu_working = False
                    break
                await asyncio.sleep(0.1)

            if imu_working:
                for c in ['Gyroscope', 'Gyroscope_accum', 'Accelerometer', 'AHRS', 'PID_steering']:
                    self.caps[c] = {
                        'fd': None,
                        'register_number': None,
                    }

            settings = load_settings()
            if isinstance(settings, dict) and 'cio' in settings:
                cio_settings = settings['cio']
                if isinstance(cio_settings, dict) and 'disabled' in cio_settings:
                    cio_disabled = cio_settings['disabled']
                    if isinstance(cio_disabled, list):
                        for disabled_component_name in cio_disabled:
                            if disabled_component_name in self.caps:
                                del self.caps[disabled_component_name]

        except:
            if self.ctlr_fd is not None:
                await easyi2c.close_i2c(self.ctlr_fd)
                self.ctlr_fd = None
                self.caps = None
            if self.batt_fd is not None:
                await easyi2c.close_i2c(self.batt_fd)
                self.batt_fd = None
            self.refcounts = {}
            self.objects = {}
            raise

        return list(self.caps.keys())

    async def acquire(self, capability_id):
        """
        Acquire the interface to the component with the given `capability_id`, and return
        a concrete object implementing its interface.
        """
        if capability_id not in self.caps:
            raise Exception(f"Unknown capability: {capability_id}")
        fd = self.caps[capability_id]['fd']
        register_number = self.caps[capability_id]['register_number']
        capability_obj = KNOWN_COMPONENTS[capability_id](fd, register_number)
        capability_obj._capability_id = capability_id
        if capability_id not in self.refcounts:
            self.refcounts[capability_id] = 1
            self.objects[capability_id] = capability_obj
            await capability_obj.acquired()
        else:
            refcount = self.refcounts[capability_id]
            self.refcounts[capability_id] = refcount + 1
        return capability_obj

    async def release(self, capability_obj):
        """
        Release a previously acquired capability interface. You must pass
        the exact object returned by `acquire()`.
        """
        capability_id = capability_obj._capability_id
        if capability_id not in self.refcounts:
            raise Exception("Invalid object passed to `release()`")
        refcount = self.refcounts[capability_id]
        refcount -= 1
        if refcount == 0:
            del self.refcounts[capability_id]
            del self.objects[capability_id]
            await capability_obj.released()
        else:
            self.refcounts[capability_id] = refcount

    async def close(self):
        """
        Close the connection and reset the controller, thereby invalidating and releasing
        all acquired components.
        """
        for capability_obj in self.objects.values():
            await capability_obj.released()

        self.refcounts = {}
        self.objects = {}

        if self.ctlr_fd is not None:
            await reset.soft_reset(self.ctlr_fd)
            await easyi2c.close_i2c(self.ctlr_fd)
            self.ctlr_fd = None
            self.caps = None

        if self.batt_fd is not None:
            await easyi2c.close_i2c(self.batt_fd)
            self.batt_fd = None

