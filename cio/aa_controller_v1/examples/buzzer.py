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

import cio.aa_controller_v1 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    b = await c.acquire('Buzzer')

    await asyncio.sleep(2)

    #await b.play()                   # defaults to the 'on' sound
    #await b.play('o4l16ceg>c8')      # the 'on' sound (explicit this time)
    #await b.play('v10>>g16>>>c16')   # the soft reset sound
    #await b.play('>E>E>E R >C>E>G')
    #await b.play('!L16 V12 cdefgab>cbagfedc')   # C-major scale up and down
    await b.play('!T240 L8 agafaea dac+adaea fa<aa<bac#a dac#adaea f4')   # "Bach's fugue in D-minor"
    await b.wait()

    await asyncio.sleep(2)

    await c.release(b)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())

