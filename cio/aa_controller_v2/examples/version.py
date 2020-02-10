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

    iface = await c.acquire('VersionInfo')
    name = await iface.name()
    version = await iface.version()
    await c.release(iface)

    await c.close()

    print(name, version)


if __name__ == '__main__':
    asyncio.run(run())

