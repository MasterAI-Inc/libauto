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
This module provides simplified implementations of the Recon sensor
and the Weapons system.

This only works on virtual cars!
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire
from auto import IS_VIRTUAL


def naive_recon(theta_1, theta_2, slice_size, max_distance):
    """
    Naive linear search using the Recon sensor.

    It returns the angle of the *first* enemy that is
    found. It returns `None` if no enemy was found.
    """
    if not IS_VIRTUAL:
        raise NotImplemented('This function only work on virtual cars.')
    recon = _get_recon()
    theta_1, theta_2 = min(theta_1, theta_2), max(theta_1, theta_2)
    for a in range(theta_1, theta_2 - slice_size + 1, slice_size):
        vins = recon.query(a, a + slice_size, max_distance)
        if vins:
            return (a + a + slice_size) / 2


def throw_ball(theta, velocity):
    """
    Simple weapons function.
    """
    if not IS_VIRTUAL:
        raise NotImplemented('This function only work on virtual cars.')
    weapons = _get_weapons()
    weapons.fire(theta=theta, phi=90, velocity=velocity)


@thread_safe
def _get_recon():
    global _RECON
    try:
        _RECON
    except NameError:
        caps = list_caps()
        if 'Recon' not in caps:
            raise AttributeError('This device has no Recon sensor!')
        _RECON = acquire('Recon')
    return _RECON


@thread_safe
def _get_weapons():
    global _WEAPONS
    try:
        _WEAPONS
    except NameError:
        caps = list_caps()
        if 'Weapons' not in caps:
            raise AttributeError('This device has no Weapons system!')
        _WEAPONS = acquire('Weapons')
    return _WEAPONS
