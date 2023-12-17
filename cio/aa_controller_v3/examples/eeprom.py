###############################################################################
#
# Copyright (c) 2017-2023 Master AI, Inc.
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

    #await c.proto.write_eeprom(4, 157)

    print(c.proto.eeprom_vals)

    print(c.proto.eeprom_read_buf(0, 256))
    print(c.proto.eeprom_read_buf(3, 5))
    print(c.proto.eeprom_read_buf(8, 5))

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

