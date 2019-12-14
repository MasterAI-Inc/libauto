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

    await asyncio.sleep(1)  # wait for reset sound to finish playing, else we block it by starting the calibration below

    calibrator = await c.acquire('Calibrator')

    await calibrator.start()
    print('Started calibration...')

    while await calibrator.check():
        print('.', end='', flush=True)
        await asyncio.sleep(1)

    print('DONE!')

    await asyncio.sleep(5)

    await c.release(calibrator)


if __name__ == '__main__':
    asyncio.run(run())

