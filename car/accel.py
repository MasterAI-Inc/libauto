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
This module provides a simplified interface to the accelerometer sensor.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def read():
    """
    Read an (x, y, z) tuple-of-floats from the Accelerometer.

    The accelerometer measures the amount of acceleration "felt" by
    the device in each axis. Measurements are in units of gravity ("G"s),
    where
      1 G = 9.81 m/s^2
    """
    return _get_accel().read()


@thread_safe
def _get_accel():
    global _ACCEL
    try:
        _ACCEL
    except NameError:
        caps = list_caps()
        if 'Accelerometer' not in caps:
            raise AttributeError('This device has no Accelerometer sensor!')
        _ACCEL = acquire('Accelerometer')
    return _ACCEL
