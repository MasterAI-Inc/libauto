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
This module connects to the car's controller via the CIO interface.

For beginners, it provides easy functions for forward, reverse, left, and right.

Advanced users may import the globals from this file and interact with the raw
CIO interfaces directly.

A future enhancement will be to create an event loop and be able to control the
car via asynchronous calls.
"""

from auto import db
from cio.rpc_client import acquire_component_interface, dispose_component_interface
import time


STORE = db.default_db(same_thread=True)

CAR_THROTTLE_FORWARD_SAFE_SPEED = STORE.get('CAR_THROTTLE_FORWARD_SAFE_SPEED', 25)
CAR_THROTTLE_REVERSE_SAFE_SPEED = STORE.get('CAR_THROTTLE_REVERSE_SAFE_SPEED', -25)


MOTORS = acquire_component_interface('CarMotors')
MOTORS.on()

PID_STEERING = acquire_component_interface('PID_steering')

GYRO_ACCUM = acquire_component_interface('Gyroscope_accum')


def straight(throttle, duration, invert_output):
    """
    Drive the car "straight". This function uses the car's gyroscope to
    continually keep the car in the same direction in which it started.

    This function is synchronous, thus it will not return until after these
    instructions are finish, which takes approximately `duration` seconds.
    """
    set_steering(0.0)
    time.sleep(0.1)
    _, _, z = GYRO_ACCUM.read()
    start_time = time.time()
    PID_STEERING.set_point(z)
    PID_STEERING.enable(invert_output=invert_output)
    while True:
        curr_time = time.time()
        if curr_time - start_time >= duration:
            break
        set_throttle(throttle)
        time.sleep(min(0.1, curr_time - start_time))
    set_throttle(0.0)
    time.sleep(0.1)
    PID_STEERING.disable()


def drive(angle, throttle, duration):
    """
    A more generic driving function.

    This function is synchronous, thus it will not return for
    approximately `duration` seconds.

    Note: If you use this function to drive the car "straight" (i.e. `angle=0`),
          the car may still veer because this function does _not_ make use of the
          car's gyroscope. This is unlike the `straight()` function, which _does_
          use the car's gyroscope.
    """
    set_steering(angle)
    time.sleep(0.1)
    start_time = time.time()
    while True:
        curr_time = time.time()
        if curr_time - start_time >= duration:
            break
        set_throttle(throttle)
        set_steering(angle)
        time.sleep(min(0.1, curr_time - start_time))
    set_throttle(0.0)
    time.sleep(0.1)


def set_steering(angle):
    """
    Set the vehicle's steering in the range [-45, 45], where -45 means
    full-right and 45 means full-left.

    THIS IS ASYNCHRONOUS. Commands sent with this function "expire" after 1 second.
    This is for safety reasons, so that the car stops if this program dies.
    """
    MOTORS.set_steering(angle)


def set_throttle(throttle):
    """
    Set the vehicle's throttle in the range [-100, 100], where -100 means
    full-reverse and 100 means full-forward.

    THIS IS ASYNCHRONOUS. Commands sent with this function "expire" after 1 second.
    This is for safety reasons, so that the car stops if this program dies.
    """
    MOTORS.set_throttle(throttle)

