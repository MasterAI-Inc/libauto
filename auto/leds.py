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
This module provides an easy way to control the LEDs on your device.

This module provides a fully **synchronous** interface.
"""

from auto.capabilities import list_caps, acquire


def led_map():
    """
    Return identifiers and descriptions of the LEDs
    available on this controller as a dictionary.
    The keys are the identifiers used to control the LEDs
    via the `set_led()` method.
    """
    return _get_leds().led_map()


def set_led(led_identifier, val):
    """
    Set the LED on/off value.
    """
    return _get_leds().set_led(led_identifier, val)


def set_many_leds(id_val_list):
    """
    Pass a list of tuples, where each tuple is an LED identifier
    and the value you want it set to.
    """
    return _get_leds().set_many_leds(id_val_list)


def mode_map():
    """
    Return identifiers and descriptions of the LED modes
    that are available as a dictionary.
    The keys are the identifiers used to set the mode
    via the `set_mode()` method.
    """
    return _get_leds().mode_map()


def set_mode(mode_identifier):
    """
    Set the `mode` of the LEDs.
    Pass `None` to clear the mode, thereby commencing
    basic on/off control via the `set_led()` method.
    """
    return _get_leds().set_mode(mode_identifier)


def set_brightness(brightness):
    """
    Set the brightness of the LEDs, in the range [0-255].
    Raises if not supported by the hardware you have.
    """
    return _get_leds().set_brightness(brightness)


def _get_leds():
    global _LEDs
    try:
        _LEDs
    except NameError:
        caps = list_caps()
        if 'LEDs' not in caps:
            raise AttributeError("This device does not have LEDs.")
        _LEDs = acquire('LEDs')
    return _LEDs

