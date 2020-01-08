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

    print('Acquiring PID_steering and CarMotors...')
    pid = await c.acquire('PID_steering')
    motors = await c.acquire('CarMotors')

    p, i, d = 1.0, 0.1, 0.1

    await pid.set_pid(p, i, d)
    await pid.set_point(0.0)

    print('Enabling PID loop...')
    await pid.enable()

    await asyncio.sleep(5)

    print('Turning on CarMotors and setting throttle...')
    await motors.on()
    await motors.set_throttle(25)

    await asyncio.sleep(10)

    print('Disabling PID loop...')
    await pid.disable()

    await asyncio.sleep(5)

    print('Turning off CarMotors...')
    await motors.off()

    await asyncio.sleep(5)

    print('Releasing PID_steering and CarMotors...')
    await c.release(pid)
    await c.release(motors)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

