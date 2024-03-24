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
This module provides simplified implementations of the LiDAR sensors.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def single(theta=0, phi=90):
    """
    Query in a single direction, denoted by `theta` and `phi`
    (using spherical coordinates), where the origin is the
    Lidar sensor's current position.

    Parameters:

     - `theta`: rotation (in degrees) in the horizontal plane;
       `theta=0` points straight "forward"; positive `theta` is
       to the left; negative `theta` is to the right.

     - `phi`: rotation (in degrees) away from the vertical axis;
       `phi=0` points straight "up" the vertical axis; positive `phi`
       moves off the vertical axis; `phi=90` lies on the horizontal
       plane; `phi=180` points opposite the vertical axis ("down").

    Returns `r` which is the distance (in meters) to the closest object
    in the direction denoted by `theta` and `phi`. Returns `r = None`
    if no object was detected.
    """
    return _get_lidar().single(theta, phi)


def sweep(theta_1=90, phi_1=90, theta_2=-90, phi_2=90):
    """
    Sweep the sensor from (`theta_1`, `phi_1`) to (`theta_2`, `phi_2`)
    and query 16 times during the sweep motion. The sensor will query
    at equal intervals along the sweep path, where the first query
    happens at (`theta_1`, `phi_1`) and the last query happens at
    (`theta_2`, `phi_2`).

    Returns a list of 16 values of `r`.

    See `single()` for a description of `theta`, `phi`, and `r`.

    Using this method `sweep()` is more efficient than calling `single()`
    over-and-over.
    """
    return _get_lidar().sweep(theta_1, phi_1, theta_2, phi_2)


@thread_safe
def _get_lidar():
    global _LIDAR
    try:
        _LIDAR
    except NameError:
        caps = list_caps()
        if 'Lidar' not in caps:
            raise AttributeError('This device has no LiDAR!')
        _LIDAR = acquire('Lidar')
    return _LIDAR
