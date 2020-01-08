###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This is a simple process which monitors the battery and updates the console
with the current battery percentage.
"""

import asyncio

from auto.services.controller.client import CioRoot
from auto.services.console.client import CuiRoot

from auto import logger
log = logger.init(__name__, terminal=True)


async def run_forever():
    controller = CioRoot()
    console = CuiRoot()

    capabilities = await controller.init()
    await console.init()

    battery = None

    try:
        if 'BatteryVoltageReader' not in capabilities:
            log.warning('No battery component exists on this device; exiting...')
            return

        log.info('RUNNING!')

        battery = await controller.acquire('BatteryVoltageReader')

        while True:
            minutes, percentage = await battery.minutes()
            await console.set_battery_percent(percentage)
            await asyncio.sleep(2)

    except asyncio.CancelledError:
        log.info('Battery monitor is being canceled...')

    finally:
        if battery is not None:
            await controller.release(battery)
            battery = None
        await controller.close()
        await console.close()


if __name__ == '__main__':
    asyncio.run(run_forever())

