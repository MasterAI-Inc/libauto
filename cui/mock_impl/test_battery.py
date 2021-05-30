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
from cui.mock_impl import CuiMock


async def run():
    c = CuiMock()
    await c.init()

    for percentage in range(0, 101):
        minutes = 2 * percentage
        await c.set_battery(state, minutes, percentage)
        await asyncio.sleep(0.01)
    for percentage in range(100, -1, -1):
        minutes = 2 * percentage
        await c.set_battery(state, minutes, percentage)
        await asyncio.sleep(0.01)


if __name__ == '__main__':
    asyncio.run(run())
