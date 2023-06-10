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

from auto.capabilities import list_caps, acquire
from auto.asyncio_tools import thread_safe
from auto import IS_VIRTUAL
import time


def sleep(seconds):
    if IS_VIRTUAL:
        physics = _physics_client()
        physics.sleep(seconds)
    else:
        time.sleep(seconds)


@thread_safe
def _physics_client():
    global _PHYSICS
    try:
        _PHYSICS
    except NameError:
        caps = list_caps()
        if 'PhysicsClient' not in caps:
            raise AttributeError('This device is not virtual!')
        _PHYSICS = acquire('PhysicsClient')
    return _PHYSICS

