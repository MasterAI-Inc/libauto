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
This module provides a simplified interface to the Compass sensor.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def query():
    """
    Query the Compass sensor.

    Returns `theta`, a single angle (in degrees) representing your
    device's deviation from magnetic north.
     - `theta = 0` means your device is pointing directly north.
     - `theta = 90` means your device is pointing directly west.
     - `theta = 180` means your device is pointing directly south.
     - `theta = 270` means your device is pointing directly east.
    """
    return _get_compass().query()


def heading():
    """
    Query the Compass sensor and return a true heading of your device.

    **ONLY AVAILABLE ON VIRTUAL DEVICES!**

    Real-world compasses cannot give you this information, but the
    "virtual" compass can. :)

    Returns a tuple (`theta`, `phi`) describing the true heading of
    your device. `theta` is an angle (in degrees) of your device's
    rotation in the world's horizontal plane. `phi` is an angle (in
    degrees) of your device's rotation away from the vertical axis.
    See `lidar.single()` for more info on the concept of `theta` and
    `phi` and on the concept of spherical coordinates.
    """
    return _get_compass().heading()


@thread_safe
def _get_compass():
    global _COMPASS
    try:
        _COMPASS
    except NameError:
        caps = list_caps()
        if 'Compass' not in caps:
            raise AttributeError('This device has no Compass!')
        _COMPASS = acquire('Compass')
    return _COMPASS
