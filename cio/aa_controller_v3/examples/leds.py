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

    leds = await c.acquire('LEDs')

    mode_map = await leds.mode_map()
    print(mode_map)

    for mode, _ in mode_map.items():
        print('Setting to mode', mode)
        await leds.set_mode(mode)
        await asyncio.sleep(7)

    print('Clearing the mode...')
    await leds.set_mode(None)

    led_map = await leds.led_map()
    print(led_map)

    print('Clearning LEDs')
    await leds.set_many_leds([(index, (0, 0, 0)) for index in led_map])
    await asyncio.sleep(1)

    print('Setting just a few manually...')
    await leds.set_led(1, (255, 145, 0))
    await asyncio.sleep(1)
    await leds.set_led(3, (0, 255, 0))
    await asyncio.sleep(1)
    await leds.set_led(5, (0, 0, 255))
    await asyncio.sleep(1)

    print('Playing with brightness!')
    for b in range(0, 255, 5):
        await leds.set_brightness(b)
        await asyncio.sleep(0.1)

    await c.release(leds)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

