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

    p = await c.acquire('Photoresistor')

    for i in range(1000):
        millivolts, resistance = await p.read()
        print(f'{millivolts:.2f} {resistance:.0f}')
        await asyncio.sleep(0.1)

    await c.release(p)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

