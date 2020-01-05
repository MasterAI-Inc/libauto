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
This script runs all the services in one process.
"""

from auto.services.camera.server import init as camera_init
from auto.services.controller.server import init as controller_init
from auto.services.console.server import init as console_init
from auto.services.labs.labs import run_forever as labs_run_forever
from auto.services.battery.monitor import run_forever as battery_run_forever

import os
import sys
import asyncio


async def init_all(system_up_user):
    # Camera Service
    camera_server = await camera_init()

    # Controller Service
    cio_server = await controller_init()

    # Console Service
    cui_server = await console_init()

    # Labs Service
    labs_task = asyncio.create_task(labs_run_forever(system_up_user))

    # Battery Monitor
    battery_task = asyncio.create_task(battery_run_forever())


if __name__ == '__main__':
    if len(sys.argv) > 1:
        system_up_user = sys.argv[1]   # the "UnPrivileged" system user
    else:
        system_up_user = os.environ['USER']

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_all(system_up_user))
    loop.run_forever()

