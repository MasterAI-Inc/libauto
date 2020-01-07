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
from auto import console as c
from auto.capabilities import acquire, release
from car import buzzer

import time
import itertools


def _query_motor_params():
    return {
        'top'             : STORE.get('CAR_MOTOR_TOP', 40000),
        'steering_left'   : STORE.get('CAR_MOTOR_STEERING_LEFT', 2100),
        'steering_mid'    : STORE.get('CAR_MOTOR_STEERING_MID', 3000),
        'steering_right'  : STORE.get('CAR_MOTOR_STEERING_RIGHT', 4100),
        'throttle_forward': STORE.get('CAR_MOTOR_THROTTLE_FORWARD', 4000),
        'throttle_mid'    : STORE.get('CAR_MOTOR_THROTTLE_MID', 3000),
        'throttle_reverse': STORE.get('CAR_MOTOR_THROTTLE_REVERSE', 2000),
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
        'p'              : STORE.get('CAR_STEERING_PID_P', 1.0),
        'i'              : STORE.get('CAR_STEERING_PID_I', 0.3),
        'd'              : STORE.get('CAR_STEERING_PID_D', 0.3),
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


def _easy_ask(prompt, curr_val, cast_func, io_device, adj_delta=1, min_val=None, max_val=None, change_callback=None):
    if io_device == 'computer':
        result = _keyboard_input(prompt=prompt,
                                 choices=None,
                                 curr_val=curr_val)
    elif io_device == 'car':
        result = _button_numeric_input(prompt=prompt,
                                       initial=curr_val,
                                       adj_delta=adj_delta,
                                       change_callback=change_callback)
    if result == curr_val:
        val = result
    else:
        val = cast_func(result)
        if max_val is not None:
            val = min(val, max_val)
        if min_val is not None:
            val = max(val, min_val)
    return val


def _calibrate_microcontroller(io_device):
    time.sleep(2)   # Allow user a few seconds to put the device down.
    calibrator = acquire('Calibrator')
    print_func = {
        'computer': print,
        'car'     : c.print,
    }[io_device]
    pinwheel = _spinning_pinwheel()
    for status in calibrator.calibrate():
        if status == '.':
            print_func(f'Calibrating [{next(pinwheel)}]', end='\r')
        else:
            print_func(status)
            if status == 'Finished microcontroller calibration!':
                break
        time.sleep(1)
    release(calibrator)
    buzzer.honk()   # Let the user know the calibration finished!


def _spinning_pinwheel():
    chars = list('-\\|/')
    while True:
        for c in chars:
            yield c


def _calibrate_safe_throttle(io_device):
    while True:
        # Ask user for new values.
        safe_forward = _easy_ask("Safe forward throttle  (0, 100]", m.CAR_THROTTLE_FORWARD_SAFE_SPEED, int,
                                 io_device, min_val=1, max_val=100)
        safe_reverse = _easy_ask("Safe reverse throttle [-100, 0)", m.CAR_THROTTLE_REVERSE_SAFE_SPEED, int,
                                 io_device, min_val=-100, max_val=-1)
        m.CAR_THROTTLE_FORWARD_SAFE_SPEED = safe_forward
        m.CAR_THROTTLE_REVERSE_SAFE_SPEED = safe_reverse
        STORE.put('CAR_THROTTLE_FORWARD_SAFE_SPEED', m.CAR_THROTTLE_FORWARD_SAFE_SPEED)
        STORE.put('CAR_THROTTLE_REVERSE_SAFE_SPEED', m.CAR_THROTTLE_REVERSE_SAFE_SPEED)

        _demo_forward_reverse_no_pid()

        if _choice_input(prompt="Keep?", choices=['n', 'y'], io_device=io_device) == 'y':
            break


def _calibrate_servo_range(io_device):
    _setup_motors()

    motor_params = _query_motor_params()
    steering_left  = motor_params['steering_left']
    steering_mid   = motor_params['steering_mid']
    steering_right = motor_params['steering_right']

    adj_delta = 10

    def demo_left(new_val):
        STORE.put('CAR_MOTOR_STEERING_LEFT', new_val)
        _setup_motors(30000)  # <-- nearabout the max possible timeout
        m.set_steering(45.0)  # <-- max left

    def demo_right(new_val):
        STORE.put('CAR_MOTOR_STEERING_RIGHT', new_val)
        _setup_motors(30000)  # <-- nearabout the max possible timeout
        m.set_steering(-45.0) # <-- max right

    def demo_mid(new_val):
        STORE.put('CAR_MOTOR_STEERING_MID', new_val)
        _setup_motors(30000)  # <-- nearabout the max possible timeout
        m.set_steering(0.0)   # <-- mid-steering ("straight")

    while True:
        demo_left(steering_left)
        v = _easy_ask("Steering left PWM value", steering_left, int, io_device, adj_delta=adj_delta, change_callback=lambda vals: demo_left(vals[0]))
        if v == steering_left:
            break  # break when the user doesn't change the value
        steering_left = v

    while True:
        demo_right(steering_right)
        v = _easy_ask("Steering right PWM value", steering_right, int, io_device, adj_delta=adj_delta, change_callback=lambda vals: demo_right(vals[0]))
        if v == steering_right:
            break  # break when the user doesn't change the value
        steering_right = v

    for i in itertools.count():
        demo_mid(steering_mid)
        if i > 0:
            _demo_forward_reverse_no_pid()
        v = _easy_ask("Steering mid PWM value", steering_mid, int, io_device, adj_delta=adj_delta, change_callback=lambda vals: demo_mid(vals[0]))
        if i > 0 and v == steering_mid:
            break  # break when the user doesn't change the value
        steering_mid = v

    _setup_motors(save=True)


def _calibrate_steering_pid(io_device):
    _setup_steering_pid()

    steering_pid_params = _query_steering_pid_params()
    p = steering_pid_params['p']
    i = steering_pid_params['i']
    d = steering_pid_params['d']

    while True:
        p, i, d = _easy_ask("Steering PID [space-separated p i d]",
                            [p, i, d],
                            lambda s: (float(v) for v in s.split(' ')),
                            io_device,
                            adj_delta=0.1)

        STORE.put('CAR_STEERING_PID_P', p)
        STORE.put('CAR_STEERING_PID_I', i)
        STORE.put('CAR_STEERING_PID_D', d)

        _setup_steering_pid()

        m.straight(m.CAR_THROTTLE_FORWARD_SAFE_SPEED, 2.5, invert_output=False)  # <-- uses gyro
        m.straight(m.CAR_THROTTLE_REVERSE_SAFE_SPEED, 2.5, invert_output=True)   # <-- uses gyro

        if _choice_input(prompt="Keep?", choices=['n', 'y'], io_device=io_device) == 'y':
            break

    _setup_steering_pid(save=True)


def calibrate(io_device=['computer', 'car'][0]):
    """
    Run the end-to-end calibration routine for this car.
    """
    _set_globals()

    if _choice_input(prompt="Do you want to calibrate your car?",
                     choices=['n', 'y'],
                     io_device=io_device) == 'n':
        msg = 'Exiting calibration.'
        _device_print(msg, io_device=io_device)
        return

    if _choice_input(prompt="Calibrate microcontroller (e.g. gyro & accelerometer)?",
                     choices=['n', 'y'],
                     io_device=io_device) == 'y':
        _calibrate_microcontroller(io_device=io_device)

    if _choice_input("Calibrate safe throttle speed?",
                     choices=['n', 'y'],
                     io_device=io_device) == 'y':
        _calibrate_safe_throttle(io_device)

    if _choice_input("Calibrate servo range?",
                     choices=['n', 'y'],
                     io_device=io_device) == 'y':
        _calibrate_servo_range(io_device)

    if _choice_input("Calibrate steering PID?",
                     choices=['n', 'y'],
                     io_device=io_device) == 'y':
        _calibrate_steering_pid(io_device)

    msg = 'Calibraton complete!'
    _device_print(msg, io_device=io_device)


def _set_globals():
    global _BUTTONS
    # assign descriptions to buttons
    _BUTTONS = {
        'LEFT/DOWN': 3,
        'SUBMIT'   : 2,
        'RIGHT/UP' : 1,
    }


def _choice_input(prompt, choices, io_device):
    if io_device == 'computer':
        result = _keyboard_input(prompt=prompt, choices=choices)
    elif io_device == 'car':
        result = _button_choice_input(prompt=prompt, choices=choices)
    return result


def _keyboard_input(prompt, choices=None, curr_val=None):
    msg_opts = msg_curr_val = ''
    if curr_val is not None:
        msg_curr_val = f' [or keep {curr_val}]: '
    if choices is not None:
        msg_opts = f" [ {' / '.join(choices)} ] "
    response = input(prompt + msg_opts + msg_curr_val)
    return response if response else curr_val


def _device_print(*args, **kwargs):
    io_device = kwargs.pop('io_device', 'computer')
    if io_device == 'computer':
        print(*args, **kwargs)
    elif io_device == 'car':
        c.print(*args, **kwargs)


def _is_pressed(button, e):
    return e['button'] == button and e['action'] == 'pressed'


def _is_released(button, e):
    return e['button'] == button and e['action'] == 'released'


def _button_choice_input(prompt, choices):
    c.print(prompt)
    choice_i = 0
    decided = False
    buttons = acquire('PushButtons')
    while not decided:
        events = buttons.get_events()
        for e in events:
            if _is_released(_BUTTONS['RIGHT/UP'], e):
                choice_i += 1
            elif _is_released(_BUTTONS['LEFT/DOWN'], e):
                choice_i -= 1
            elif _is_released(_BUTTONS['SUBMIT'], e):
                decided = True
                break
            if abs(choice_i) == len(choices):
                choice_i = 0
        output = f"[ {' / '.join([(f'({c})' if i == abs(choice_i) else f' {c} ') for i, c in enumerate(choices)])} ]"
        c.print(output, end='\r' if not decided else '\n')
        time.sleep(0.05)
    release(buttons)
    return choices[choice_i]


def _button_numeric_input(prompt, initial=0, adj_delta=1, change_callback=None):
    TIMER_RESET_VAL = 15
    adj_factor = [1, 10, 100]  # increase increment/decrement amount by factor
    adj = adj_rate = extra_delay = val_idx = 0
    vals = [initial] if not isinstance(initial, list) else initial
    val = vals[val_idx]
    still_editing = True
    held = False
    c.print(prompt)
    buttons = acquire('PushButtons')
    while still_editing:
        events = buttons.get_events()
        if events:
            for e in events:
                if _is_released(_BUTTONS['SUBMIT'], e):
                    if val_idx + 1 == len(vals):
                        still_editing = False
                    else:
                        val_idx += 1
                        val = vals[val_idx]
                if _is_released(_BUTTONS['LEFT/DOWN'], e) or _is_released(_BUTTONS['RIGHT/UP'], e):
                    held = False
                    adj = 0
                    adj_rate = 0
                    extra_delay = 0
                if _is_pressed(_BUTTONS['LEFT/DOWN'], e):
                    held = True
                    timer = TIMER_RESET_VAL
                    adj = -adj_delta
                if _is_pressed(_BUTTONS['RIGHT/UP'], e):
                    held = True
                    timer = TIMER_RESET_VAL
                    adj = adj_delta
                val += adj * adj_factor[adj_rate]
        else:
            val += adj * (adj_factor[adj_rate])
        if isinstance(adj_delta, float):
            val = round(val, len(str(adj_delta)) - 2)
        if held:
            if timer != 0:
                timer -= 1
            else:
                if val % (10 * adj_delta) == 0:
                    adj_rate = min([adj_rate + 1, len(adj_factor)])
                    extra_delay = 0.50  # give more time for humans to react
                    timer = TIMER_RESET_VAL
        vals[val_idx] = val
        output = f"[ {' / '.join([f'({v})' if i == val_idx else f' {v} ' for i, v in enumerate(vals)])} ]"
        if change_callback is not None:
            change_callback(vals)
        c.print(output, end='\r')
        time.sleep(0.05 + extra_delay)

    c.print('Finished choosing', vals)
    release(buttons)
    return vals[0] if len(vals) == 1 else ' '.join(str(v) for v in vals)

