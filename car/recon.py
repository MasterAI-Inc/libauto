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
This module provides a simplified interface to the Reconnaissance ("Recon")
sensor.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire
from car import IS_VIRTUAL


def query(theta_1=90, theta_2=-90, r=10000):
    """
    Detect enemy devices within a certain space around your
    device, as defined by `theta_1`, `theta_2`, and `r`.

    The space queried ranges in your device's horizontal
    plane from `theta_1` to `theta_2` (both in degrees)
    and extends `r` meters away from your device.

    These "theta" values (in degrees) affect the sensor's
    detection space around your device's horizontal plane:
     - `theta = 0` is "forward" of your device
     - `theta = 90` is "directly left"
     - `theta = -90` is "directly right"

    For example, querying with `theta_1 = 45` and `theta_2 = -45`
    will query a 90-degree circular sector in front of your device.

    Another example, querying with `theta_1 = 0` and `theta_2 = 360`
    will query for *all* devices near you, no matter what angle they
    are from you.

    Another example, querying with `theta_1 = 90` and `theta_2 = 270`
    will query in the half-circle space "behind" your device.

    The `r` value (a distance in meters) affects the sensor's query
    radius from your device. E.g. `r = 100` will detect enemy devices
    within 100 meters of your device.

    Note: To precisely locate an enemy, you can binary search the
          `theta_*` space, then binary search the `r` space.

    This query returns a list of device VINs which were found in the
    queried space. An empty list is returned if no devices are found.
    """
    return _get_recon().query(theta_1, theta_2, r)


def naive_recon(theta_1, theta_2, slice_size, max_distance):
    """
    Naive linear search using the Recon sensor.

    It returns the angle of the *first* enemy that is
    found. It returns `None` if no enemy was found.
    """
    if not IS_VIRTUAL:
        raise NotImplemented('This function only work on virtual cars.')
    theta_1, theta_2 = min(theta_1, theta_2), max(theta_1, theta_2)
    for a in range(theta_1, theta_2 - slice_size + 1, slice_size):
        vins = query(a, a + slice_size, max_distance)
        if vins:
            return (a + a + slice_size) / 2


@thread_safe
def _get_recon():
    global _RECON
    try:
        _RECON
    except NameError:
        caps = list_caps()
        if 'Recon' not in caps:
            raise AttributeError('This device has no Reconnaissance ("Recon") sensor!')
        _RECON = acquire('Recon')
    return _RECON
