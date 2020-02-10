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

import cio.aa_controller_v2 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    b = await c.acquire('PushButtons')

    print('There are', await b.num_buttons(), 'buttons.')

    bi, action = await b.wait_for_action('released')

    print("Button", bi, "was", action)

    while True:
        event = await b.wait_for_event()
        pprint(event)

    await c.release(b)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

