###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################


import os
import subprocess


SCRIPTS_DIRECTORY = os.path.dirname(os.path.realpath(__file__))


def run_script(path, *args, timeout=5):
    if not os.path.isfile(path):
        return 'Error: The script or program at the specified path is not installed on your system.'

    try:
        cmd = [path, *args]
        output = subprocess.run(cmd,
                                timeout=timeout,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT).stdout.decode('utf-8')
        return output

    except subprocess.TimeoutExpired:
        return 'Error: Command timed out...'

