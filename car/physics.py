###############################################################################
#
# Copyright (c) 2017-2024 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module exposes the interface to the virtual device's physics engine.

**ONLY WORKS ON VIRTUAL DEVICES!**
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire
from car import IS_VIRTUAL


def wait_tick():
    """
    Wait until the next physics engine "tick". The physics
    engine does 20 updates per second (each is called a "tick"),
    and it sends a message to us after each update. Thus, this
    method simply waits for the next message to arrive and then
    returns. You can use this method to do computation in lock-step
    with the physics engine, as it is silly to do certain things
    faster than the physics engine (e.g. querying GPS) since updates
    only happen after each "tick".
    """
    return _get_physics().wait_tick()


def sleep(seconds):
    """
    Sleeps for approximately `seconds` by counting "ticks" from the
    physics engine. This provides a way to sleep in lock-step with
    the physics engine to minimize drift.
    """
    return _get_physics().sleep(seconds)


def respawn(x, y, z, r):
    """
    Respawn your device at this location:
     - x: the x-coordinate
     - y: the y-coordinate
     - z: the z-coordinate
     - r: the rotation (in degrees)

    **NOTE:** You may not respawn in all circumstances. E.g. In some contests,
              you might get penalized or disqualified, so be cautious when you
              use this function!
    """
    return _get_physics().control({
        'type': 'respawn_device',
        'x': x,
        'y': y,
        'z': z,
        'r': r,
    })


@thread_safe
def _get_physics():
    if not IS_VIRTUAL:
        raise NotImplemented('This function only work on virtual devices!')
    global _PHYSICS
    try:
        _PHYSICS
    except NameError:
        caps = list_caps()
        if 'PhysicsClient' not in caps:
            raise AttributeError('This device has no PhysicsClient!')
        _PHYSICS = acquire('PhysicsClient')
    return _PHYSICS
