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

    iface = await c.acquire('VersionInfo')
    name = await iface.name()
    version = await iface.version()
    await c.release(iface)

    print(name, version)


if __name__ == '__main__':
    asyncio.run(run())

