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
This module provides a simplified interface to the magnetometer sensor.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def read():
    """
    Read an (x, y, z) tuple-of-floats from the Magnetometer.
    """
    return _get_mag().read()


@thread_safe
def _get_mag():
    global _MAG
    try:
        _MAG
    except NameError:
        caps = list_caps()
        if 'Magnetometer' not in caps:
            raise AttributeError('This device has no Magnetometer sensor!')
        _MAG = acquire('Magnetometer')
    return _MAG
