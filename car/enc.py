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
This module provides simplified implementations of the Encoder sensors.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def num_encoders():
    """
    Return the number of Encoders on this controller.
    """
    return _get_encoders().num_encoders()


def enable(index):
    """
    Enable an encoder. The first encoder is index-0.
    """
    return _get_encoders().enable(index)


def read(index):
    """
    Read the counts of the encoder. The first encoder is index-0.
    The count is reset to zero when the encoder is enabled.

    Returns the number of "clicks" (a signed value) that this encoder has seen.
    """
    return _get_encoders().read(index)[0]


def disable(index):
    """
    Disable an encoder. The first encoder is index-0.
    """
    return _get_encoders().disable(index)


@thread_safe
def _get_encoders():
    global _ENCODERS
    try:
        _ENCODERS
    except NameError:
        caps = list_caps()
        if 'Encoders' not in caps:
            raise AttributeError('This device has no Encoders!')
        _ENCODERS = acquire('Encoders')
    return _ENCODERS
