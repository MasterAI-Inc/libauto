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
from cio.aa_controller_v1 import default_handle as h

pprint(h.CAPS)

loop = h.acquire_component_interface('LoopFrequency')

for i in range(50):
    print(loop.read())
    time.sleep(0.05)

gyro = h.acquire_component_interface('Gyroscope')

for i in range(50):
    print(loop.read())
    time.sleep(0.05)

accel = h.acquire_component_interface('Accelerometer')

for i in range(50):
    print(loop.read())
    time.sleep(0.05)

h.dispose_component_interface(gyro)
h.dispose_component_interface(accel)

for i in range(50):
    print(loop.read())
    time.sleep(0.05)

