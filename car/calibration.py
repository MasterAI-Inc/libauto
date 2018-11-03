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
This module contains an end-to-end calibration routine for the car.
"""

from car.motors import STORE
from car import motors as m

from cio import rpc_client as cio_rpc_client

import sys


def _query_motor_params():
    return {
        'top'              : STORE.get('CAR_MOTOR_TOP',              40000),
        'steering_left'    : STORE.get('CAR_MOTOR_STEERING_LEFT',     3600),
        'steering_mid'     : STORE.get('CAR_MOTOR_STEERING_MID',      3000),
        'steering_right'   : STORE.get('CAR_MOTOR_STEERING_RIGHT',    2400),
        'throttle_forward' : STORE.get('CAR_MOTOR_THROTTLE_FORWARD',  4000),
        'throttle_mid'     : STORE.get('CAR_MOTOR_THROTTLE_MID',      3000),
        'throttle_reverse' : STORE.get('CAR_MOTOR_THROTTLE_REVERSE',  2000),
    }


def _setup_motors(millisecond_timeout=1000, save=False):
    motor_params = _query_motor_params()
    m.MOTORS.set_params(
            steering_millis  = millisecond_timeout,
            throttle_millis  = millisecond_timeout,
            **motor_params
    )
    if save:
        m.MOTORS.save_params()


def _query_steering_pid_params():
    return {
        'p':               STORE.get('CAR_STEERING_PID_P', 2.0),
        'i':               STORE.get('CAR_STEERING_PID_I', 0.0),
        'd':               STORE.get('CAR_STEERING_PID_D', 0.0),
        'error_accum_max': STORE.get('CAR_STEERING_PID_EAM', 0.0),
    }


def _setup_steering_pid(save=False):
    steering_pid_params = _query_steering_pid_params()
    m.PID_STEERING.set_pid(
            **steering_pid_params
    )
    if save:
        m.PID_STEERING.save_pid()


def _demo_forward_reverse_no_pid(duration=1.0):
    m.drive(0.0, m.CAR_THROTTLE_FORWARD_SAFE_SPEED, duration)
    m.drive(0.0, m.CAR_THROTTLE_REVERSE_SAFE_SPEED, duration)


def _easy_ask(prompt, curr_val, cast_func):
    typed = input("{} [or keep {}]: ".format(prompt, curr_val)).strip()
    if len(typed) == 0:
        val = curr_val
    else:
        val = cast_func(typed)
    return val


def _calibrate_microcontroller():
    calibrator = cio_rpc_client.acquire_component_interface('Calibrator')
    cio_rpc_client.redirect_stdio(stdout=sys.stdout)
    calibrator.calibrate()
    cio_rpc_client.restore_stdio()
    cio_rpc_client.dispose_component_interface(calibrator)


def _calibrate_safe_throttle():
    while True:
        # Ask user for new values.
        safe_forward = _easy_ask("Safe forward throttle  (0, 100]", m.CAR_THROTTLE_FORWARD_SAFE_SPEED, int)
        safe_reverse = _easy_ask("Safe reverse throttle [-100, 0)", m.CAR_THROTTLE_REVERSE_SAFE_SPEED, int)
        m.CAR_THROTTLE_FORWARD_SAFE_SPEED = safe_forward
        m.CAR_THROTTLE_REVERSE_SAFE_SPEED = safe_reverse
        STORE.put('CAR_THROTTLE_FORWARD_SAFE_SPEED', m.CAR_THROTTLE_FORWARD_SAFE_SPEED)
        STORE.put('CAR_THROTTLE_REVERSE_SAFE_SPEED', m.CAR_THROTTLE_REVERSE_SAFE_SPEED)

        _demo_forward_reverse_no_pid()

        if input("Keep? [n/y] ") == 'y':
            break


def _calibrate_servo_range():
    _setup_motors()

    motor_params = _query_motor_params()
    steering_left  = motor_params['steering_left']
    steering_mid   = motor_params['steering_mid']
    steering_right = motor_params['steering_right']

    _setup_motors(30000)
    m.set_steering(45.0)
    v = _easy_ask("Steering left PWM value", steering_left, int)
    while True:
        steering_left = v
        STORE.put('CAR_MOTOR_STEERING_LEFT', steering_left)
        _setup_motors(30000)  # <-- nearabout the max possible timeout
        m.set_steering(45.0)
        v = _easy_ask("Steering left PWM value", steering_left, int)
        if v == steering_left:
            break  # break when the user doesn't change the value

    _setup_motors(30000)
    m.set_steering(-45.0)
    v = _easy_ask("Steering right PWM value", steering_right, int)
    while True:
        steering_right = v
        STORE.put('CAR_MOTOR_STEERING_RIGHT', steering_right)
        _setup_motors(30000)  # <-- nearabout the max possible timeout
        m.set_steering(-45.0)
        v = _easy_ask("Steering right PWM value", steering_right, int)
        if v == steering_right:
            break  # break when the user doesn't change the value

    _setup_motors()
    m.set_steering(0)
    v = _easy_ask("Steering mid PWM value", steering_mid, int)
    while True:
        steering_mid = v
        STORE.put('CAR_MOTOR_STEERING_MID', steering_mid)
        _setup_motors()
        _demo_forward_reverse_no_pid()
        v = _easy_ask("Steering mid PWM value", steering_mid, int)
        if v == steering_mid:
            break  # break when the user doesn't change the value

    _setup_motors(save=True)


def _calibrate_steering_pid():
    _setup_steering_pid()

    steering_pid_params = _query_steering_pid_params()
    p = steering_pid_params['p']
    i = steering_pid_params['i']
    d = steering_pid_params['d']

    while True:
        p, i, d = _easy_ask("Steering PID [space-separated p i d]", (p, i, d), lambda s: tuple(float(v) for v in s.split(' ')))

        STORE.put('CAR_STEERING_PID_P', p)
        STORE.put('CAR_STEERING_PID_I', i)
        STORE.put('CAR_STEERING_PID_D', d)

        _setup_steering_pid()

        m.forward(2.5)  # <-- uses gyro
        m.reverse(2.5)  # <-- uses gyro

        if input("Keep? [n/y] ") == 'y':
            break

    _setup_steering_pid(save=True)


def calibrate():
    """
    Run the end-to-end calibration routine for this car.
    """

    if input("Calibrate microcontroller (e.g. gyro & accelerometer)? [n/y] ") == 'y':
        _calibrate_microcontroller()

    if input("Calibrate safe throttle speed? [n/y] ") == 'y':
        _calibrate_safe_throttle()

    if input("Calibrate servo range? [n/y] ") == 'y':
        _calibrate_servo_range()

    if input("Calibrate steering PID? [n/y] ") == 'y':
        _calibrate_steering_pid()

