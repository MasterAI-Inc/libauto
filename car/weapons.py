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
This module provides a simplified interface to the device's weapons.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def fire(theta=0, phi=90, velocity=40):
    """
    Fire your device's default weapon in the direction
    defined by `theta` and `phi` (both in degrees) and
    with a velocity of `velocity` (in meters/second).

    See `lidar.single()` for a description of `theta`
    and `phi`.
    """
    return _get_weapons().fire(theta, phi, velocity)


@thread_safe
def _get_weapons():
    global _WEAPONS
    try:
        _WEAPONS
    except NameError:
        caps = list_caps()
        if 'Weapons' not in caps:
            raise AttributeError('This device has no Weapons!')
        _WEAPONS = acquire('Weapons')
    return _WEAPONS
