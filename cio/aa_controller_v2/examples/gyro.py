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


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    gyro       = await c.acquire('Gyroscope')
    gyro_accum = await c.acquire('Gyroscope_accum')

    for i in range(500):
        print(await gyro.read())
        print(await gyro_accum.read())
        print()
        if i % 50 == 0:
            await gyro_accum.reset()
        await asyncio.sleep(0.1)

    await c.release(gyro)
    await c.release(gyro_accum)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

