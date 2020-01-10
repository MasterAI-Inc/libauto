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
This is a simple process which monitors the off switch and shuts down the device
as soon as off switch is triggered.
"""

import asyncio

import RPi.GPIO as GPIO

from auto import logger
log = logger.init(__name__, terminal=True)

from auto.services.labs.util import _shutdown


BCM_PIN = 26


async def run_forever():
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BCM_PIN, GPIO.IN, GPIO.PUD_UP)

    log.info('RUNNING!')

    while True:
        val = GPIO.input(BCM_PIN)
        if val == 0:
            log.info('Off switch triggered; shutting down...')
            output = _shutdown(reboot=False)
            log.info('Shutdown command output: {}'.format(output))
            return
        await asyncio.sleep(0.2)


if __name__ == '__main__':
    asyncio.run(run_forever())

