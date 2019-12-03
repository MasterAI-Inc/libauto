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

leds = h.acquire_component_interface('LEDs')

leds.set_mode(1)

time.sleep(3)

leds.set_mode(0)
leds.set_values()

time.sleep(1)

for i in range(8):
    binary = "{0:{fill}3b}".format(i, fill='0')
    red, green, blue = [int(b) for b in binary]
    leds.set_values(red, green, blue)
    time.sleep(1)

