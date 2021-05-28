###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import asyncio
from pprint import pprint

import cio.aa_controller_v3 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    power = await c.acquire('Power')

    for i in range(1000):
        st = await power.state()
        mv = await power.millivolts()
        mi = await power.estimate_remaining()
        sd = await power.should_shut_down()
        print(st, mv, mi, sd)
        await asyncio.sleep(0.1)

    await c.release(power)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

