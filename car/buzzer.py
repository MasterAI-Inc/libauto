###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
This module provides a simple helper to use the buzzer.
"""

from cio.rpc_client import acquire_component_interface

BUZZER = acquire_component_interface('Buzzer')


def buzz(notes):
    """
    Play the given `notes` on the device's buzzer.
    """
    BUZZER.play(notes)
    BUZZER.wait()


def honk(count=1):
    """
    Make a car horn ("HONK") sound.
    """
    MAX_HONKS = 5
    count = min(MAX_HONKS, count)
    for _ in range(count - 1):
        buzz('!T95 O4 G#16 R16') # short honk
    buzz('!T95 O4 G#4') # final long honk
