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

gyro       = h.acquire_component_interface('Gyroscope')
gyro_accum = h.acquire_component_interface('Gyroscope_accum')

for i in range(1000):
    print(gyro.read())
    print(gyro_accum.read())
    print()
    time.sleep(0.1)

