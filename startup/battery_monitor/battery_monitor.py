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

from auto import console as c
from auto import print_all

from cio.rpc_client import acquire_component_interface

from auto.db import default_db
STORE = default_db()

from auto import logger
log = logger.init('battery_monitor', terminal=True)


log.info("Starting battery monitoring process...")


if STORE.get('BATTERY_MONITOR_DISABLED', False):
    log.info("Battery monitor is disabled on this device... exiting.")
    sys.exit()


BATTERY_HIGH_MILLIVOLTS = STORE.get('BATTERY_HIGH_MILLIVOLTS', 8400)
BATTERY_LOW_MILLIVOLTS =  STORE.get('BATTERY_LOW_MILLIVOLTS',  6500)

log.info("Battery high millivolts: {}".format(BATTERY_HIGH_MILLIVOLTS))
log.info("Battery low millivolts:  {}".format(BATTERY_LOW_MILLIVOLTS))


buzz = acquire_component_interface("Buzzer")
batt = acquire_component_interface("BatteryVoltageReader")


def batt_voltage_to_pct(millivolts):
    """
    Take in millivolts (an integer) and
    return percentage (an integer in [0, 100]).

    See: https://github.com/AutoAutoAI/libauto/issues/7
    """
    high = BATTERY_HIGH_MILLIVOLTS
    low  = BATTERY_LOW_MILLIVOLTS
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

