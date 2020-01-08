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

    # Put up a big full-screen image by passing an image-path.
    await c.big_image('wifi_success')
    await asyncio.sleep(2)

    # Put up some big text!
    for i in range(1, 5):
        text = "All is good... {}".format(i)
        await c.big_status(text)
        await asyncio.sleep(1)

    # Clear the big text.
    await c.big_status('')
    await asyncio.sleep(2)

    # Clear the screen of the big image and text.
    await c.big_clear()
    await asyncio.sleep(2)


if __name__ == '__main__':
    asyncio.run(run())
