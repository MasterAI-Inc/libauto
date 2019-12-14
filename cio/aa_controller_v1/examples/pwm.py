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

    pwm = await c.acquire('PWMs')

    n = await pwm.num_pins()

    print("# PWM-capable pins:", n)

    frequency = 50   # Hz

    for pin_index in range(n):
        print('Running on pin #', pin_index)

        await pwm.enable(pin_index, frequency)

        for i in range(10):
            for duty in range(5, 10):
                await pwm.set_duty(pin_index, duty)
                await asyncio.sleep(0.1)

        await asyncio.sleep(2)

        await pwm.disable(pin_index)

    await c.release(pwm)


async def run01():
    caps = await c.init()
    pprint(caps)

    pwm = await c.acquire('PWMs')

    frequency = 20000   # Hz

    await pwm.enable(0, frequency)
    await pwm.enable(1, frequency)

    for j in range(100):
        for i in range(41):
            await pwm.set_duty(0, 15+i)
            await pwm.set_duty(1, 40+i)
            await asyncio.sleep(0.1)
        for i in range(40, -1, -1):
            await pwm.set_duty(0, 15+i)
            await pwm.set_duty(1, 40+i)
            await asyncio.sleep(0.1)

    #await asyncio.sleep(100)

    await pwm.disable(0)
    await pwm.disable(1)

    await c.release(pwm)


async def run13():
    caps = await c.init()
    pprint(caps)

    pwm = await c.acquire('PWMs')

    frequency = 20000   # Hz

    await pwm.enable(1, frequency)
    await pwm.enable(3, frequency//2)

    for j in range(100):
        for i in range(41):
            await pwm.set_duty(1, 15+i)
            await pwm.set_duty(3, 40+i)
            await asyncio.sleep(0.1)
        for i in range(40, -1, -1):
            await pwm.set_duty(1, 15+i)
            await pwm.set_duty(3, 40+i)
            await asyncio.sleep(0.1)

    #await asyncio.sleep(100)

    await pwm.disable(1)
    await pwm.disable(3)

    await c.release(pwm)


if __name__ == '__main__':
    asyncio.run(run())
    #asyncio.run(run01())
    #asyncio.run(run13())

