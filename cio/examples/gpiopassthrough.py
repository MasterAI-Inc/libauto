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

gpio = h.acquire_component_interface('GpioPassthrough')

gpio.print_all_state(n_pins=20)  # the mini-mode exposes only 20 pins
print('-' * 70)

rx = gpio.employ_pin(0)
tx = gpio.employ_pin(1)

buttons = gpio.employ_pin(18)
vindiv2 = gpio.employ_pin(19)

while True:
    print(buttons.analog_read())
    #print(vindiv2.analog_read())
    time.sleep(0.1)

