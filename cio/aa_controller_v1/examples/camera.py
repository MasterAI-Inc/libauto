###############################################################################
#
# Copyright (c) 2017-2021 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import asyncio
from pprint import pprint

import cio.aa_controller_v1 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    camera = await c.acquire('Camera')
    frame = await camera.capture()
    await c.release(camera)

    await c.close()

    print(frame)


if __name__ == '__main__':
    asyncio.run(run())

