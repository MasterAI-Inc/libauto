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

from auto import console as c
from auto import print_all

from cio.rpc_client import acquire_component_interface

from auto import logger
log = logger.init('wifi_controller', terminal=True)


log.info("Starting battery monitoring process...")


buzz = acquire_component_interface("Buzzer")
batt = acquire_component_interface("BatteryVoltageReader")


def batt_voltage_to_pct(millivolts):
    """
    Take in millivolts (an integer) and
    return percentage (an integer in [0, 100]).
    """
    high = 8400
    low = 6500
    if millivolts > high:
        return 100
    if millivolts < low:
        return 0
    return int(round((millivolts - low) / (high - low) * 100))


while True:

    millivolts = batt.millivolts()
    percentage = batt_voltage_to_pct(millivolts)

    log.info("Battery millivolts={}, percentage={}".format(millivolts, percentage))

    c.set_battery_percent(percentage)

    if percentage < 10:
        buzz.play("EEE")
        print_all("Warning: Battery <10%")

    time.sleep(10)

