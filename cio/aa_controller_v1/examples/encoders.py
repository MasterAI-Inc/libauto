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

import cio.aa_controller_v1 as controller


async def run():
    c = controller.CioRoot()
    caps = await c.init()
    pprint(caps)

    enc = await c.acquire('Encoders')

    enc_index = 1   # the _second encoder

    n = await enc.num_encoders()
    print('# encoders:', n)

    await enc.enable(enc_index)

    def fmt(val):
        return "{:6d}".format(val)

    for i in range(100000):
        counts = await enc.read_counts(enc_index)
        counts_str = ''.join([fmt(c) for c in counts])

        timing = await enc.read_timing(enc_index)
        timing_str = ''.join([fmt(t) for t in timing])

        print(counts_str + timing_str)

        await asyncio.sleep(0.1)

    await enc.disable(enc_index)

    await c.release(enc)

    await c.close()


if __name__ == '__main__':
    asyncio.run(run())



### DRIVE THE CAR

# from car import motors
#
# ...
#
# while True:
#     throttle, steering = await enc.read_timing(1)
#     throttle = (throttle - 1500) / 500 * 100
#     steering = (steering - 1500) / 500 * 45
#     motors.set_throttle(throttle)
#     motors.set_steering(steering)
#
# ...

