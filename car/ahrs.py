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
This module provides a simplified interface to the
Attitude and Heading Reference System (AHRS).
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def read():
    """
    Get the current (roll, pitch, yaw) tuple-of-floats of the device.

    This component, if present, will provide more accurate data than
    the `Gyroscope_accum` component as it may use more sensors and/or
    more sophisticated calculations.

    Each of (roll, pitch, yaw) is given in degrees and is relative to the
    device's resting position.
    """
    return _get_ahrs().read()


@thread_safe
def _get_ahrs():
    global _AHRS
    try:
        _AHRS
    except NameError:
        caps = list_caps()
        if 'AHRS' not in caps:
            raise AttributeError('This device has no AHRS!')
        _AHRS = acquire('AHRS')
    return _AHRS
