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
This module contains functions to run external script/programs. This module
assumes a certain setup of the system, but it tries to fail gracefully if the
system is not configured as expected.

**NOTE:** All paths here should be specified absolutely. Relative paths
          can create vulnerabilities.
"""

import subprocess
import asyncio
import re
import os

from auto.services.scripts import SCRIPTS_DIRECTORY


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
    return _run_command(path, name)


def _shutdown(reboot):
    path = '/sbin/reboot' if reboot else '/sbin/poweroff'
    return _run_command(path)


def _update_libauto():
    path = os.path.join(SCRIPTS_DIRECTORY, 'update_libauto'
    return _run_command(path)


def _run_command(path, *args):
    if not os.path.isfile(path):
        return 'Error: The script or program at the specified path is not installed on your system.'

    try:
        cmd = [path, *args]
        output = subprocess.run(cmd,
                                timeout=5,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).stdout.decode('utf-8')
        return output

    except subprocess.TimeoutExpired:
        return 'Error: Command timed out...'

