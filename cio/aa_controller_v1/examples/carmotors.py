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

    motors = await c.acquire('CarMotors')

    await motors.set_params(
            top              = 40000,
            steering_left    = 3600,
            steering_mid     = 3000,
            steering_right   = 2400,
            steering_millis  = 1000,
            throttle_forward = 4000,
            throttle_mid     = 3000,
            throttle_reverse = 2000,
            throttle_millis  = 1000,
    )
    await motors.save_params()

    await motors.on()

    await asyncio.sleep(1)

    for i in range(2):
        for v in range(-45, 45):
            print(v)
            await motors.set_steering(v)
            await motors.set_throttle(20)
            await asyncio.sleep(0.02)
        for v in range(45, -45, -1):
            print(v)
            await motors.set_steering(v)
            await motors.set_throttle(20)
            await asyncio.sleep(0.02)

    await motors.off()

    await asyncio.sleep(3)

    await c.release(motors)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

