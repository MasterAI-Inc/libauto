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

    motors = await c.acquire('CarMotors')

    await motors.on()

    await asyncio.sleep(1)

    t = 70

    for i in range(2):
        for v in range(-45, 45):
            #print(v)
            await motors.set_steering(v)
            await motors.set_throttle(t)
            await asyncio.sleep(0.02)
        for v in range(45, -45, -1):
            #print(v)
            await motors.set_steering(v)
            await motors.set_throttle(t)
            await asyncio.sleep(0.02)

    await motors.off()

    await asyncio.sleep(3)

    await c.release(motors)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

