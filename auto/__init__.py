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


__version__ = '2.7.0'

IS_VIRTUAL = os.environ.get('MAI_IS_VIRTUAL', 'False').lower() in ['true', 't', '1', 'yes', 'y']


def print_all(*args, **kwargs):
    """
    Prints to both standard out (as the build-in `print` does by default), and
    also prints to the AutoAuto console!
    """
    from auto.console import print as aa_console_print
    aa_console_print(*args, **kwargs)
    print(*args, **kwargs)

