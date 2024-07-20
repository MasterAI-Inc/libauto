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
This module provides a simplified interface to the Photoresistor sensor.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def read():
    """
    Read the voltage of the photoresistor pin, and read
    the computed resistance of the photoresistor. Return
    both as a two-tuple `(millivolts, ohms)`.
    """
    return _get_photoresistor().read()


def read_millivolts():
    """
    Read the raw voltage of the photoresistor pin.
    """
    return _get_photoresistor().read_millivolts()


def read_ohms():
    """
    Read the resistance of the photoresistor (in ohms). The photoresistor's
    resistance changes depending on how much light is on it, thus the name!
    """
    return _get_photoresistor().read_ohms()


@thread_safe
def _get_photoresistor():
    global _PHOTORESISTOR
    try:
        _PHOTORESISTOR
    except NameError:
        caps = list_caps()
        if 'Photoresistor' not in caps:
            raise AttributeError('This device has no Photoresistor sensor!')
        _PHOTORESISTOR = acquire('Photoresistor')
    return _PHOTORESISTOR
