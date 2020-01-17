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
This package contains a mock CIO interface implementing only the required
components.
"""

import random

import cio
from cio.aa_controller_v1.components import Credentials


class CioRoot(cio.CioRoot):
    """
    This is a mock CIO interface.

    All components are mock _except_ for the Credentials component, which uses
    the implementation from `aa_controller_v1`. This is so that we can still
    properly authenticate even if we fall to this mock implementation.
    """

    def __init__(self):
        # These are the only required components.
        self.impls = {
            'VersionInfo': VersionInfo(),
            'Credentials': Credentials(None, None),
            'LoopFrequency': LoopFrequency(),
            'BatteryVoltageReader': BatteryVoltageReader(),
        }

    async def init(self):
        return list(self.impls.keys())

    async def acquire(self, capability_id):
        return self.impls[capability_id]

    async def release(self, capability_obj):
        pass

    async def close(self):
        pass


class VersionInfo(cio.VersionInfoIface):

    async def name(self):
        return "Mock CIO Implementation"

    async def version(self):
        return (0, 1)


class LoopFrequency(cio.LoopFrequencyIface):

    async def read(self):
        return random.randint(150, 180)


class BatteryVoltageReader(cio.BatteryVoltageReaderIface):

    async def millivolts(self):
        return random.randint(7000, 8000)

    async def estimate_remaining(self, millivolts=None):
        if millivolts is None:
            millivolts = self.millivolts()
        batt_low, batt_high = 6500, 8400
        pct_estimate = (millivolts - batt_low) / (batt_high - batt_low)
        pct_estimate = max(min(pct_estimate, 1.0), 0.0)
        mins_estimate  = pct_estimate * 3.5 * 60.0   # assumes a full battery lasts 3.5 hours
        return int(round(mins_estimate)), int(round(pct_estimate * 100))

    async def should_shut_down(self):
        return False

