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

import cio.aa_controller_v2 as controller


def fmt(vals):
    print(''.join(f'{v:10.2f}' for v in vals))


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    accel = await c.acquire('Accelerometer')

    for i in range(1000):
        fmt(await accel.read())
        await asyncio.sleep(0.05)

    await c.release(accel)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

