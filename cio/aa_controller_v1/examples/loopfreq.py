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

import cio.aa_controller_v1 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    loop = await c.acquire('LoopFrequency')

    for i in range(50):
        print(await loop.read())
        await asyncio.sleep(0.05)

    gyro = await c.acquire('Gyroscope')

    for i in range(50):
        print(await loop.read())
        await asyncio.sleep(0.05)

    accel = await c.acquire('Accelerometer')

    for i in range(50):
        print(await loop.read())
        await asyncio.sleep(0.05)

    await c.release(gyro)
    await c.release(accel)

    for i in range(50):
        print(await loop.read())
        await asyncio.sleep(0.05)

    await c.release(loop)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

