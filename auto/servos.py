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
This module provides an easy way to control the servos of your device. This
only works for standard "hobby style" servos which are controlled via PWM.

This module provides a fully **synchronous** interface.
"""


from auto.asyncio_tools import thread_safe
from auto.capabilities import list_caps, acquire
import time


@thread_safe
def get_servo(servo_index, frequency=50, min_duty=0.025, max_duty=0.125):
    """
    Acquire the interface to the servo at index `servo_index`.
    The first servo is at index 0.
    """
    global _PWMs
    try:
        _PWMs
    except NameError:
        caps = list_caps()
        if 'PWMs' not in caps:
            raise AttributeError("This device does not have a PWM controller.")
        _PWMs = acquire('PWMs')

    n_pins = _PWMs.num_pins()

    if servo_index < 0 or servo_index >= n_pins:
        raise Exception("Invalid servo index given: {}. This device has servos 0 through {}".format(servo_index, n_pins-1))

    return _ServoTemplate(
            _PWMs,
            servo_index,
            frequency,
            min_duty,
            max_duty
    )


class _ServoTemplate:
    def __init__(self, pwms, pin_index, frequency, min_duty, max_duty):
        self._pwms = pwms
        self._pin_index = pin_index
        self._frequency = frequency
        self._min_duty = min_duty
        self._max_duty = max_duty
        self._is_on = False

    def on(self):
        """
        Enable power to the servo!
        """
        if not self._is_on:
            self._pwms.enable(self._pin_index, self._frequency)
            self._is_on = True

    def off(self):
        """
        Disable power from the servo!"
        """
        if self._is_on:
            self._pwms.disable(self._pin_index)
            self._is_on = False

    def go(self, position):
        """
        Set the `position` of the servo in the range [0, 180].
        These `position` roughly corresponds to the angle of the servo.
        You may pass an integer or a float to the `position` parameter.
        """
        if self._is_on:
            val = min(180.0, position)
            val = max(0.0, position)
            val = (val / 180.0) * (self._max_duty - self._min_duty) + self._min_duty
            val = val * 100.0
            self._pwms.set_duty(self._pin_index, val)
        else:
            raise Exception("You must turn the servo on by calling the `on()` method before you can tell the servo to `go()`!")

    def wait(self, seconds):
        """
        Pause and wait for `seconds` seconds.
        You may pass an integer or a float to the `seconds` parameter.
        """
        time.sleep(seconds)

    def go_then_wait(self, position, seconds):
        """
        First set the servo's position to the `position` value,
        then wait `seconds` seconds.
        See the `go()` method for a description of the `position` parameter.
        See the `wait()` method for a description of the `seconds` parameter.
        """
        self.go(position)
        self.wait(seconds)

