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
import time
from pprint import pprint

import cio.aa_controller_v3 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    iface = await c.acquire('VersionInfo')

    n = 0
    start = time.time()

    while True:
        _ = await iface.version()
        n += 1
        now = time.time()
        if (now - start) >= 1.0:
            print(n)
            start = now
            n = 0

    await c.release(iface)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

