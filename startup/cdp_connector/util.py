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
import re


def set_hostname(name):
    name = re.sub(r'[^A-Za-z0-9]', '', name)
    output = subprocess.run(['set_hostname', name],
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT).stdout.decode('utf-8')
    return output

