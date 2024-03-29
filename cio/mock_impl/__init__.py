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

import asyncio
import random
import subprocess

import numpy as np

import cio
from cio.aa_controller_v1.components import Credentials

from cio.aa_controller_v1.camera_async import CameraRGB_Async
from cio.aa_controller_v1.camera_pi import CameraRGB


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
            'VersionInfo': VersionInfo,
            'Credentials': lambda: Credentials(None, None),
            'Camera': Camera,
            'Power': Power,
        }

    async def init(self):
        return list(self.impls.keys())

    async def acquire(self, capability_id):
        return self.impls[capability_id]()

    async def release(self, capability_obj):
        pass

    async def close(self):
        pass


class VersionInfo(cio.VersionInfoIface):

    async def name(self):
        return "Mock CIO Implementation"

    async def version(self):
        return (0, 1)


class Camera(cio.CameraIface):
    _camera = None

    def __init__(self):
        if Camera._camera is None:
            loop = asyncio.get_running_loop()
            Camera._camera = CameraRGB_Async(
                    lambda: CameraRGB(width=320, height=240, fps=8),
                    loop=loop,
                    idle_timeout=30
            )

    async def capture(self):
        return await Camera._camera.capture()


class Power(cio.PowerIface):

    async def state(self):
        return 'wall'

    async def millivolts(self):
        return random.randint(7000, 8000)

    async def estimate_remaining(self, millivolts=None):
        if millivolts is None:
            millivolts = await self.millivolts()
        batt_low, batt_high = 6500, 8400
        pct_estimate = (millivolts - batt_low) / (batt_high - batt_low)
        pct_estimate = max(min(pct_estimate, 1.0), 0.0)
        mins_estimate  = pct_estimate * 3.5 * 60.0   # assumes a full battery lasts 3.5 hours
        return int(round(mins_estimate)), int(round(pct_estimate * 100))

    async def should_shut_down(self):
        return False

    async def shut_down(self):
        subprocess.run(['/sbin/poweroff'])

    async def reboot(self):
        subprocess.run(['/sbin/reboot'])

