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
"""

import subprocess
import asyncio
import re
import os


async def set_hostname(name):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _set_hostname, name)


def _set_hostname(name):
    PATH = '/usr/local/bin/set_hostname'

    if not os.path.isfile(PATH):
        return 'The `set_hostname` script not installed; hostname not set.'

    name = re.sub(r'[^A-Za-z0-9]', '', name)

    try:
        output = subprocess.run(['sudo', PATH, name],
                                timeout=5,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).stdout.decode('utf-8')
        return output

    except subprocess.TimeoutExpired:
        return 'Command timed out...'

