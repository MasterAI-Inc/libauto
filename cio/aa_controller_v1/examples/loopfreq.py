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

import cio.aa_controller_v1 as c


async def run():
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


if __name__ == '__main__':
    asyncio.run(run())

