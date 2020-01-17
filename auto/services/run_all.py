###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This script runs all the services in one process.
"""

from auto.services.camera.server import init as camera_init
from auto.services.controller.server import init as controller_init
from auto.services.console.server import init as console_init
from auto.services.labs.labs import init_and_create_forever_task as labs_init_and_create_forever_task
from auto.services.battery.monitor import run_forever as battery_run_forever
from auto.services.wifi.monitor import run_forever as wifi_run_forever
from auto.services.jupyter.run import run_jupyter_in_background

import os
import sys
import asyncio


async def init_all(system_up_user, system_priv_user):
    # Camera Service
    camera_server = await camera_init()

    # Controller Service
    cio_server = await controller_init()

    # Console Service
    cui_server = await console_init()

    # Labs Service
    labs_forever_task = await labs_init_and_create_forever_task(system_up_user)

    # Battery Monitor
    battery_task = asyncio.create_task(battery_run_forever())

    # Wifi Monitor
    wifi_task = asyncio.create_task(wifi_run_forever(system_priv_user))

    # Jupyter
    jupyter_thread = run_jupyter_in_background(system_up_user)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        system_up_user = sys.argv[1]   # the "UnPrivileged" system user
    else:
        system_up_user = os.environ['USER']

    if len(sys.argv) > 2:
        system_priv_user = sys.argv[2]   # the "Privileged" system user
    else:
        system_priv_user = os.environ['USER']

    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_all(system_up_user, system_priv_user))
    loop.run_forever()

