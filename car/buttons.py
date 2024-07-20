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
This module provides a simplified interface to the car's buttons.
"""

from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire


def num_buttons():
    """
    Return the number of buttons on the device.
    """
    return _get_buttons().num_buttons()


def button_state(button_index):
    """
    Return the state of the button at the given index (zero-based).
    Returns a tuple of (num_presses, num_releases, is_currently_pressed)
    which are of types (int, int, bool).
    """
    return _get_buttons().button_state(button_index)


def get_events():
    """
    Return a list of buttons events that have happened since
    the last call this method. The returned list will be empty
    if no events have transpired.
    """
    return _get_buttons().get_events()


def wait_for_event():
    """
    Wait for the next event, and return it once it occurs.
    """
    return _get_buttons().wait_for_event()


def wait_for_action(action='pressed'):
    """
    Wait for a certain button action to happen.

    The `action` may be one of:
        - "pressed" : Wait for a button to be pressed.
                      This is the default.
        - "released": Wait for a button to be released.
        - "any"     : Wait for either a button to be pressed or released,
                      whichever happens first.

    A two-tuple is returned `(button_index, action)`, where
    `button_index` is the zero-based index of the button on which
    the action occurred, and `action` is either "pressed" or "released".
    """
    return _get_buttons().wait_for_action(action)


@thread_safe
def _get_buttons():
    global _BUTTONS
    try:
        _BUTTONS
    except NameError:
        caps = list_caps()
        if 'PushButtons' not in caps:
            raise AttributeError('This device has no buttons!')
        _BUTTONS = acquire('PushButtons')
    return _BUTTONS
