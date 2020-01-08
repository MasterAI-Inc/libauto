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
from cui.pygame_impl import CuiPyGame


async def run():
    c = CuiPyGame()
    await c.init()

    for i in range(0, 101):
        await c.set_battery_percent(i)
        await asyncio.sleep(0.01)
    for i in range(100, -1, -1):
        await c.set_battery_percent(i)
        await asyncio.sleep(0.01)


if __name__ == '__main__':
    asyncio.run(run())
