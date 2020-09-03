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
This module connects to the car's controller via the CIO interface.

For beginners, it provides easy functions for forward, reverse, left, and right.
"""

from auto.capabilities import list_caps, acquire
import time


ENCODER_INDEX = 1               # PCB's index for the encoder
ENCODER_CPR = 28                # Encoder's counts per revolution (CPR)
MOTOR_RATIO = 100               # Motor's internal gearbox ratio; e.g. if "100:1", then just 100
WHEEL_CIRCUMFERENCE = 197.92    # In millimeters
INVERT_ENCODER = -1             # 1 or -1; specific to how the encoder is installed.


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


def straight(throttle, sec, cm, invert_output=False):
    """
    Drive the car "straight". This function uses the car's gyroscope to
    continually keep the car in the same direction in which it started.

    This function is synchronous, thus it will not return until after the
    car has completed the desired motion.
    """
    pid_steering = _get_pid_steering()
    gyro_accum = _get_gyro_accum()
    set_steering(0.0)
    time.sleep(0.1)
    _, _, z = gyro_accum.read()
    start_time = time.time()
    pid_steering.set_point(z)
    pid_steering.enable(invert_output=invert_output)

    if sec:
        while True:
            curr_time = time.time()
            if curr_time - start_time >= sec:
                break
            set_throttle(throttle)
            time.sleep(min(0.1, curr_time - start_time))

    elif cm:
        start_distance = current_distance_cm()
        throttle_time = time.time()
        set_throttle(throttle)
        while abs(current_distance_cm() - start_distance) < cm:
            curr_time = time.time()
            if curr_time - throttle_time > 0.75:
                set_throttle(throttle)
                throttle_time = curr_time

    set_throttle(0.0)
    time.sleep(0.1)
    pid_steering.disable()


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
    set_steering(angle)
    time.sleep(0.1)
    start_time = time.time()

    if sec:
        while True:
            curr_time = time.time()
            if curr_time - start_time >= sec:
                break
            set_throttle(throttle)
            set_steering(angle)
            time.sleep(min(0.1, curr_time - start_time))

    elif deg:
        gyro = _get_gyro_accum()
        gyro.reset()  # Start the gyroscope reading at 0.
        throttle_time = time.time()
        set_throttle(throttle)
        while True:
            x, y, z = gyro.read()
            if abs(z) >= deg:
                break
            curr_time = time.time()
            if curr_time - throttle_time > 0.75:
                set_throttle(throttle)
                set_steering(angle)
                throttle_time = curr_time

    set_throttle(0.0)
    time.sleep(0.1)


def current_distance_cm():
    """
    Use the encoder to calculate how far the car has travels
    since bootup.
    """
    encoder = _get_encoder()
    curr_count, _, _ = encoder.read_counts(ENCODER_INDEX)

    # Convert `curr_count` to linear distance (in mm).
    curr_distance = (curr_count / ENCODER_CPR) * (WHEEL_CIRCUMFERENCE / MOTOR_RATIO)

    # mm to cm
    curr_distance /= 10

    return curr_distance * INVERT_ENCODER


def set_steering(angle):
    """
    Set the vehicle's steering in the range [-45, 45], where -45 means
    full-right and 45 means full-left.

    THIS IS ASYNCHRONOUS. Commands sent with this function "expire" after 1 second.
    This is for safety reasons, so that the car stops if this program dies.
    """
    motors = _get_motors()
    motors.set_steering(angle)


def set_throttle(throttle):
    """
    Set the vehicle's throttle in the range [-100, 100], where -100 means
    full-reverse and 100 means full-forward.

    THIS IS ASYNCHRONOUS. Commands sent with this function "expire" after 1 second.
    This is for safety reasons, so that the car stops if this program dies.
    """
    motors = _get_motors()
    motors.set_throttle(throttle)


def _get_motors():
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


def _safe_throttle_range():
    global _SAFE_REVERSE, _SAFE_FORWARD
    try:
        _SAFE_REVERSE, _SAFE_FORWARD
    except NameError:
        motors = _get_motors()
        _SAFE_REVERSE, _SAFE_FORWARD = _MOTORS.get_safe_throttle()
    return _SAFE_REVERSE, _SAFE_FORWARD


def _get_pid_steering():
    global _PID_STEERING
    try:
        _PID_STEERING
    except NameError:
        caps = list_caps()
        if 'PID_steering' not in caps:
            raise AttributeError('This device has no PID steering loop.')
        _PID_STEERING = acquire('PID_steering')
    return _PID_STEERING


def _get_gyro_accum():
    global _GYRO_ACCUM
    try:
        _GYRO_ACCUM
    except NameError:
        caps = list_caps()
        if 'Gyroscope_accum' not in caps:
            raise AttributeError('This device has no gyroscope.')
        _GYRO_ACCUM = acquire('Gyroscope_accum')
    return _GYRO_ACCUM


def _get_encoder():
    global _ENCODER
    try:
        _ENCODER
    except NameError:
        caps = list_caps()
        if 'Encoders' not in caps:
            raise AttributeError('This device has no encoder.')
        _ENCODER = acquire('Encoders')
        _ENCODER.enable(ENCODER_INDEX)
    return _ENCODER

