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
This module contains functions to run external script/programs. This module
assumes a certain setup of the system, but it tries to fail gracefully if the
system is not configured as expected.

**NOTE:** All paths here should be specified absolutely. Relative paths
          can create vulnerabilities.
"""

import os
import re
import asyncio

from auto.services.scripts import SCRIPTS_DIRECTORY, run_script


async def set_hostname(name):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _set_hostname, name)


async def shutdown(reboot=False):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _shutdown, reboot)


async def update_libauto():
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _update_libauto)


def _set_hostname(name):
    path = os.path.join(SCRIPTS_DIRECTORY, 'set_hostname')
    name = re.sub(r'[^A-Za-z0-9]', '', name)
    return run_script(path, name)


def _shutdown(reboot):
    path = '/sbin/reboot' if reboot else '/sbin/poweroff'
    return run_script(path)


def _update_libauto():
    path = os.path.join(SCRIPTS_DIRECTORY, 'update_libauto')
    return run_script(path)

