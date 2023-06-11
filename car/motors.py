###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module connects to the car's controller via the CIO interface.

For beginners, it provides easy functions for forward, reverse, left, and right.
"""

from auto.capabilities import list_caps, acquire
from auto.asyncio_tools import thread_safe


def safe_forward_throttle():
    """
    Return a "safe" throttle values for driving forward, where "safe" means
    the resulting speed will be slow enough for the typical indoor classroom
    environment.

    **Disclaimer:** Any and all movement of the vehicle can result in injury
                    if proper safety precautions are not taken. It is the
                    responsibility of the user to use the device in a safe
                    manner at all times.
    """
    safe_reverse, safe_forward = _safe_throttle_range()
    return safe_forward


def safe_reverse_throttle():
    """
    Return a "safe" throttle value for driving in reverse.

    **IMPORTANT:** See the notes and disclaimer about "safe" in the function
                   documentation for `safe_forward_throttle()` as the same notes
                   and disclaimer applies to this this function as well.
    """
    safe_reverse, safe_forward = _safe_throttle_range()
    return safe_reverse


def straight(throttle, sec, cm):
    """
    Drive the car "straight". This function uses the car's gyroscope to
    continually keep the car in the same direction in which it started.

    This function is synchronous, thus it will not return until after the
    car has completed the desired motion.
    """
    car_control = _get_car_control()
    return car_control.straight(throttle, sec, cm)


def drive(angle, throttle, sec, deg):
    """
    Drive at a given wheel angle (`angle`) and at a given throttle (`throttle`)
    for a given duration (`sec`) or degrees (`deg`).

    This function is synchronous, thus it will not return until after the
    car has completed the desired motion.

    Note: If you use this function to drive the car "straight" (i.e. `angle=0`),
          the car may still veer because this function does _not_ make use of the
          car's gyroscope. This is unlike the `straight()` function, which _does_
          use the car's gyroscope.
    """
    car_control = _get_car_control()
    return car_control.drive(angle, throttle, sec, deg)


def set_steering(angle):
    """
    Set the vehicle's steering in the range [-45, 45], where -45 means
    full-right and 45 means full-left.

    THIS IS ASYNCHRONOUS. Commands sent with this function "expire" after 1 second.
    This is for safety reasons, so that the car stops if this program dies.
    """
    motors = _get_car_motors()
    motors.set_steering(angle)


def set_throttle(throttle):
    """
    Set the vehicle's throttle in the range [-100, 100], where -100 means
    full-reverse and 100 means full-forward.

    THIS IS ASYNCHRONOUS. Commands sent with this function "expire" after 1 second.
    This is for safety reasons, so that the car stops if this program dies.
    """
    motors = _get_car_motors()
    motors.set_throttle(throttle)


@thread_safe
def _get_car_control():
    global _CAR_CONTROL
    try:
        _CAR_CONTROL
    except NameError:
        caps = list_caps()
        if 'CarControl' not in caps:
            raise AttributeError('This device is not a car.')
        _CAR_CONTROL = acquire('CarControl')
        _CAR_CONTROL.on()
    return _CAR_CONTROL


@thread_safe
def _get_car_motors():
    global _MOTORS
    try:
        _MOTORS
    except NameError:
        caps = list_caps()
        if 'CarMotors' not in caps:
            raise AttributeError('This device is not a car.')
        _MOTORS = acquire('CarMotors')
        _MOTORS.on()
    return _MOTORS


@thread_safe
def _safe_throttle_range():
    global _SAFE_REVERSE, _SAFE_FORWARD
    try:
        _SAFE_REVERSE, _SAFE_FORWARD
    except NameError:
        motors = _get_car_motors()
        _SAFE_REVERSE, _SAFE_FORWARD = motors.get_safe_throttle()
    return _SAFE_REVERSE, _SAFE_FORWARD

