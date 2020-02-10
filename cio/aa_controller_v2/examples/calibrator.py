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

    await asyncio.sleep(1)  # wait for reset sound to finish playing, else we block it by starting the calibration below

    calibrator = await c.acquire('Calibrator')

    await calibrator.start()
    print('Started calibration...')

    while True:
        status = await calibrator.status()
        if status == -1:
            # Indicates we are done calibrating.
            break
        print('.', end='', flush=True)
        await asyncio.sleep(1)

    print('DONE!')

    await asyncio.sleep(5)

    await c.release(calibrator)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

