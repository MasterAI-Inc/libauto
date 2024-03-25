###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This model provides a context-aware sleep function.

On physical devices, it uses the standard `time.sleep()` function.

On virtual devices, it counts physics-engine "ticks" so that we
stay in-sync with the physics engine to minimize the amount of
drift and thereby maximize the amount of reproducibility.
"""

from auto import IS_VIRTUAL
from car import physics
import time


def sleep(seconds):
    if IS_VIRTUAL:
        physics.sleep(seconds)
    else:
        time.sleep(seconds)
