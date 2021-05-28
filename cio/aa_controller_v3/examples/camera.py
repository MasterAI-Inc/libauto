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
import time
import numpy as np

import cio.aa_controller_v3 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    camera = await c.acquire('Camera')

    prev_time = time.time()

    for i in range(10):
        buf, shape = await camera.capture()
        frame = np.frombuffer(buf, dtype=np.uint8).reshape(shape)
        time_now = time.time()
        print(time_now - prev_time, frame.shape)
        prev_time = time_now

    await c.release(camera)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

