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

    p = await c.acquire('Photoresistor')

    for i in range(1000):
        print(await p.read(), await p.read_millivolts(), await p.read_ohms())
        await asyncio.sleep(0.1)

    await c.release(p)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

