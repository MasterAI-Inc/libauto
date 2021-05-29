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


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    iface = await c.acquire('Credentials')

    labs_auth_code = await iface.get_labs_auth_code()
    print('Labs Auth Code:', labs_auth_code)

    await iface.set_labs_auth_code('something')

    labs_auth_code = await iface.get_labs_auth_code()
    print('Labs Auth Code:', labs_auth_code)

    await c.release(iface)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

