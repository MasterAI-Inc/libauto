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

motors = h.acquire_component_interface('CarMotors')

motors.set_params(
        top              = 40000,
        steering_left    = 3600,
        steering_mid     = 3000,
        steering_right   = 2400,
        steering_millis  = 1000,
        throttle_forward = 4000,
        throttle_mid     = 3000,
        throttle_reverse = 2000,
        throttle_millis  = 1000,
)
motors.save_params()

motors.on()

time.sleep(1)

for i in range(2):
    for v in range(-45, 45):
        print(v)
        motors.set_steering(v)
        motors.set_throttle(20)
        time.sleep(0.02)
    for v in range(45, -45, -1):
        print(v)
        motors.set_steering(v)
        motors.set_throttle(20)
        time.sleep(0.02)

motors.off()

time.sleep(3)

