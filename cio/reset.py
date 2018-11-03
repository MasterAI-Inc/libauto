###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

from . import capabilities
from .easyi2c import i2c_poll_until


def soft_reset(fd):
    """
    Instruct the controller to reset itself. This is a software-reset only.
    """
    capabilities.soft_reset(fd)
    i2c_poll_until(lambda: capabilities.is_ready(fd), True, timeout_ms=1000)

