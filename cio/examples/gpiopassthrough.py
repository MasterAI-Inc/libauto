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

rx.set_mode_input(True)
tx.set_mode_input(True)

buttons = gpio.employ_pin(18)
vindiv2 = gpio.employ_pin(19)

# while True:
#     print(buttons.analog_read())
#     #print(vindiv2.analog_read())
#     time.sleep(0.1)

rx_prev = rx.digital_read()
tx_prev = tx.digital_read()

while True:
    rx_now = rx.digital_read()
    tx_now = tx.digital_read()

    if rx_now != rx_prev:
        print("RX is", 1 if rx_now else 0)
        rx_prev = rx_now

    if tx_now != tx_prev:
        print("TX is", 1 if tx_now else 0)
        tx_prev = tx_now

