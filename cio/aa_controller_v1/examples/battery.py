###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import asyncio
from pprint import pprint

import cio.aa_controller_v1 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    batt = await c.acquire('BatteryVoltageReader')

    for i in range(100):
        mv = await batt.millivolts()
        mi = await batt.minutes()
        print(mv, mi)
        await asyncio.sleep(0.1)

    await c.release(batt)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

