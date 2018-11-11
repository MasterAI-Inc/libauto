###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import time
from pprint import pprint
from cio import default_handle as h

pprint(h.CAPS)

enc = h.acquire_component_interface('Encoders')

enc.enable_e2()

def fmt(val):
    return "{:6d}".format(val)

while True:
    print(''.join([fmt(val) for val in enc.read_e2_counts()]))
    print()
    time.sleep(0.1)


### DRIVE THE CAR

# from car import motors

# while True:
#     throttle, steering = enc.read_e2_timing()
#     throttle = (throttle - 1500) / 500 * 100
#     steering = (steering - 1500) / 500 * 45
#     motors.set_throttle(throttle)
#     motors.set_steering(steering)

