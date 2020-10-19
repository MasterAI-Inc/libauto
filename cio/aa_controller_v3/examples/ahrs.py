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

import cio.aa_controller_v3 as controller


def fmt(vals):
    names = ['roll', 'pitch', 'yaw']
    print(''.join(f'{n}={v:<10.2f}' for n, v in zip(names, vals)))


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    ahrs = await c.acquire('AHRS')

    for i in range(10000):
        fmt(await ahrs.read())
        await asyncio.sleep(0.05)

    await c.release(ahrs)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

