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

    b = await c.acquire('PushButtons')

    bi, action = await b.wait_for_action('released')

    print("Button", bi, "was", action)

    while True:
        event = await b.wait_for_event()
        pprint(event)

    await c.release(b)


if __name__ == '__main__':
    asyncio.run(run())

