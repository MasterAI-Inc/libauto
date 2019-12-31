###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import subprocess
import asyncio
import re
import os


async def set_hostname(name):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _set_hostname, name)


def _set_hostname(name):
    """
    The official Master AI image has the `set_hostname` script installed
    at the path used below.
    """
    PATH = '/usr/local/bin/set_hostname'

    if not os.path.isfile(PATH):
        return 'The `set_hostname` script not installed; hostname not set.'

    name = re.sub(r'[^A-Za-z0-9]', '', name)
    output = subprocess.run(['sudo', PATH, name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).stdout.decode('utf-8')
    return output

