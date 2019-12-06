###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

from auto.capabilities import list_caps, acquire, release
import time


_TIMER_1 = None
_TIMER_3 = None

_SERVOS = {}


def get_servo(servo_index):
    """
    Acquire the interface to the servo at index `servo_index`.
    The first servo is at index 0.
    """
    global _TIMER_1, _TIMER_3

    if servo_index in _SERVOS:
        return _SERVOS[servo_index]

    if servo_index in (0, 1, 2):
        if _TIMER_1 is None:
            _TIMER_1 = acquire('Timer1PWM')
        timer = _TIMER_1

        if servo_index == 0:
            servo = _ServoTemplate(
                    timer.set_top,
                    timer.set_ocr_a,
                    timer.enable_a,
                    timer.disable_a,
                    40000,
                    1000,
                    5000
            )
        elif servo_index == 1:
            servo = _ServoTemplate(
                    timer.set_top,
                    timer.set_ocr_b,
                    timer.enable_b,
                    timer.disable_b,
                    40000,
                    1000,
                    5000
            )
        elif servo_index == 2:
            servo = _ServoTemplate(
                    timer.set_top,
                    timer.set_ocr_c,
                    timer.enable_c,
                    timer.disable_c,
                    40000,
                    1000,
                    5000
            )

        _SERVOS[servo_index] = servo
        return servo

    elif servo_index == 3:
        if _TIMER_3 is None:
            _TIMER_3 = acquire('Timer3PWM')
        timer = _TIMER_3
        servo = _ServoTemplate(
                timer.set_top,
                timer.set_ocr,
                timer.enable,
                timer.disable,
                40000,
                1000,
                5000
        )
        _SERVOS[servo_index] = servo
        return servo

    else:
        raise Exception("Invalid servo index given: {}".format(servo_index))


class _ServoTemplate:
    def __init__(self, set_top, set_ocr, enable, disable, top_val, min_val, max_val):
        self._set_top = set_top
        self._set_ocr = set_ocr
        self._enable  = enable
        self._disable = disable
        self._top_val = top_val
        self._min_val = min_val
        self._max_val = max_val
        self._is_on = False
        self._last_val = 0

    def on(self):
        """
        Enable power to the servo!
        """
        if not self._is_on:
            self._set_top(self._top_val)
            self._set_ocr(self._last_val)
            self._enable()
            self._is_on = True

    def off(self):
        """
        Disable power from the servo!"
        """
        if self._is_on:
            self._disable()
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
            val = (val / 180.0) * (self._max_val - self._min_val) + self._min_val
            val = int(round(val))
            self._set_ocr(val)
            self._last_val = val
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

