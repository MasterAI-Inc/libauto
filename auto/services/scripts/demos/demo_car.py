###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
Demo steering the car. Note: This script must run before anything else
has launched, thus we launch our own controller server here (and let
it die once this script terminates).
"""

from auto.services.controller.server import init as controller_init

from auto.asyncio_tools import get_loop
import asyncio

from car.motors import set_steering
import time


def demo_steering():
    time.sleep(3.5)

    set_steering(-45.0)
    time.sleep(1.0)

    set_steering(45.0)
    time.sleep(1.0)

    set_steering(0.0)
    time.sleep(2.0)


if __name__ == '__main__':
    loop = get_loop()
    future = asyncio.run_coroutine_threadsafe(controller_init(), loop)
    _ = future.result()
    demo_steering()

