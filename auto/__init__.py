###############################################################################
#
# Copyright (c) 2017-2022 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import os


__version__ = '2.10.0'

IS_VIRTUAL = os.environ.get('MAI_IS_VIRTUAL', 'False').lower() in ['true', 't', '1', 'yes', 'y']


def print_all(*args, **kwargs):
    """
    Prints to both standard out (as the build-in `print` does by default), and
    also prints to the AutoAuto console!
    """
    from auto.console import print as aa_console_print
    aa_console_print(*args, **kwargs)
    print(*args, **kwargs)


def _ctx_print_all(*args, **kwargs):
    """
    This function does `print_all` on regular devices,
    but prints only to stdout on virtual devices.

    Why? Because we don't want so much printing to the
    "console" on virtual devices, since virtual devices
    don't have a standard LCD screen for the console UI,
    thus printing to the console on virtual devices is
    more "in your face" and can be distracting if we print
    too much to it.
    """
    if IS_VIRTUAL:
        print(*args, **kwargs)
    else:
        print_all(*args, **kwargs)

