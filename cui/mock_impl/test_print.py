###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import sys
import asyncio
from cui.mock_impl import CuiMock


async def run():
    c = CuiMock()
    await c.init()

    while True:
        try:
            text = sys.stdin.readline()
        except KeyboardInterrupt:
            await c.clear_text()
            break

        await c.write_text(text)

    await asyncio.sleep(2)


if __name__ == '__main__':
    asyncio.run(run())
