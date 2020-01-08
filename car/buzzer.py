###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module provides a simple helper to use the buzzer.
"""

from auto.capabilities import list_caps, acquire


def buzz(notes):
    """
    Play the given `notes` on the device's buzzer.
    """
    global _BUZZER
    try:
        _BUZZER
    except NameError:
        caps = list_caps()
        if 'Buzzer' not in caps:
            raise AttributeError("This device does not have a buzzer.")
        _BUZZER = acquire('Buzzer')
    _BUZZER.play(notes)
    _BUZZER.wait()


def honk(count=1):
    """
    Make a car horn ("HONK") sound.
    """
    MAX_HONKS = 5
    count = min(MAX_HONKS, count)
    for _ in range(count - 1):
        buzz('!T95 O4 G#16 R16') # short honk
    buzz('!T95 O4 G#4') # final long honk
