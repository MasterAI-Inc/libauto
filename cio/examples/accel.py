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

accel = h.acquire_component_interface('Accelerometer')

for i in range(1000):
    print(accel.read())
    time.sleep(0.1)

