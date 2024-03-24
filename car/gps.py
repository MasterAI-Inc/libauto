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
This module provides simplified implementations of the GPS sensors.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def query():
    """
    Query the GPS sensor. The return value depends on the type of device
    you are using:

    For *physical* devices, the return value is a point using the
    *Geographic coordinate system*, thus it is a three-tuple:
        (`latitude`, `longitude`, `altitude`)

    For *virtual* devices, the return value is a point using the
    *Cartesian coordinate system*, thus it is a three-tuple:
        (`x`, `y`, `z`)
    """
    return _get_gps().query()


@thread_safe
def _get_gps():
    global _GPS
    try:
        _GPS
    except NameError:
        caps = list_caps()
        if 'GPS' not in caps:
            raise AttributeError('This device has no GPS!')
        _GPS = acquire('GPS')
    return _GPS
