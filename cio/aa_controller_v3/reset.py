###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

from . import capabilities
from .easyi2c import i2c_poll_until


async def soft_reset(fd):
    """
    Instruct the controller to reset itself. This is a software-reset only.
    """
    await capabilities.soft_reset(fd)

    async def _is_ready():
        return await capabilities.is_ready(fd)

    await i2c_poll_until(_is_ready, True, timeout_ms=1000)

