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
        await asyncio.sleep(3)

    print('Clearing the mode...')
    await leds.set_mode(None)

    led_map = await leds.led_map()
    print(led_map)

    print('Turning on red...')
    await leds.set_led('red', True)
    await asyncio.sleep(2)

    print('Turning off red...')
    await leds.set_led('red', False)

    await asyncio.sleep(1)

    for i in range(8):
        binary = "{0:{fill}3b}".format(i, fill='0')
        print('Showing binary:', binary)
        red, green, blue = [int(b) for b in binary]
        await leds.set_many_leds(zip(['red', 'green', 'blue'], [red, green, blue]))
        await asyncio.sleep(1)

    await c.release(leds)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

