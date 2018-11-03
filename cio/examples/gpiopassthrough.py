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

gpio()
print('-' * 70)

red   = gpio.employ_pin(16)
green = gpio.employ_pin(7)
blue  = gpio.employ_pin(15)

buttons = gpio.employ_pin(18)

blue.set_output(True)

while True:
    print(buttons.analog_read())
    time.sleep(0.1)

