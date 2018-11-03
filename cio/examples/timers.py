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
import sys
from pprint import pprint
from cio import default_handle as h

pprint(h.CAPS)


t1 = h.acquire_component_interface('Timer1PWM')

t1.set_top(20000)
t1.set_ocr_b(3000)
t1.enable_b()

time.sleep(2)

for i in range(0, 20000, 100):
    t1.set_ocr_b(i)
    time.sleep(0.01)

t1.set_ocr_b(3000)

time.sleep(2)

time.sleep(2)


t3 = h.acquire_component_interface('Timer3PWM')

t3.set_top(20000)
t3.set_ocr(3000)
t3.enable()

time.sleep(2)

for i in range(0, 20000, 100):
    t3.set_ocr(i)
    time.sleep(0.01)

t3.set_ocr(3000)

time.sleep(1)

t3.set_range(2000, 4000)

for i in range(0, 100):
    t3(i / 100)
    time.sleep(0.01)

t3.set_ocr(3000)

time.sleep(2)

t3.disable()

time.sleep(2)

t1.disable_b()

time.sleep(2)

