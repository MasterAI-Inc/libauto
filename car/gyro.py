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
This module provides simplified implementations of the gyroscrope sensor.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def read():
    """
    Read an (x, y, z) tuple-of-floats from the Gyroscope.

    The gyroscope measures the instantaneous rotational velocity
    that this device is experiencing right now.

        x = rotational velocity around the x-axis (degrees per second)
        y = rotational velocity around the y-axis (degrees per second)
        z = rotational velocity around the z-axis (degrees per second)
    """
    return _get_gyro().read()


def read_accum():
    """
    Read the accumulated (x, y, z) tuple-of-floats from the Gyroscope.

    This component accumulates the gyroscope data over time to provide
    an absolute rotational angel of this device (relative to when this
    component was last "reset").

        x = current rotation around the x-axis (degrees)
        y = current rotation around the y-axis (degrees)
        z = current rotation around the z-axis (degrees)
    """
    return _get_gyro_accum().read()


def reset_accum():
    """
    Reset the (x, y, z) accumulators back to zero.
    """
    return _get_gyro_accum().reset()


@thread_safe
def _get_gyro():
    global _GYRO
    try:
        _GYRO
    except NameError:
        caps = list_caps()
        if 'Gyroscope' not in caps:
            raise AttributeError('This device has no Gyroscope sensor!')
        _GYRO = acquire('Gyroscope')
    return _GYRO


@thread_safe
def _get_gyro_accum():
    global _GYRO_ACCUM
    try:
        _GYRO_ACCUM
    except NameError:
        caps = list_caps()
        if 'Gyroscope_accum' not in caps:
            raise AttributeError('This device has no Gyroscope sensor!')
        _GYRO_ACCUM = acquire('Gyroscope_accum')
    return _GYRO_ACCUM
