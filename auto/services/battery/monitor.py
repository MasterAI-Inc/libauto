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
This is a simple process which monitors the battery and updates the console
with the current battery percentage.
"""

import asyncio

from auto.services.controller.client import CioRoot
from auto.services.console.client import CuiRoot

from auto.services.labs.rpc.client import LabsService

from auto import logger
log = logger.init(__name__, terminal=True)


def _gen_sample_sizes():
    yield 3
    while True:
        yield 10


async def _display_forever(power, console, labs, buzzer):
    for sample_size in _gen_sample_sizes():
        samples = []

        for _ in range(sample_size):
            millivolts = await power.millivolts()
            samples.append(millivolts)
            await asyncio.sleep(3)

        millivolts = sum(samples) / len(samples)
        minutes, percentage = await power.estimate_remaining(millivolts)
        state = await power.state()

        await console.set_battery(minutes, percentage)
        await labs.send({
            'type': 'battery_state',
            'state': state,
            'minutes': minutes,
            'percentage': percentage,
        })
        if percentage <= 5:
            await console.write_text("Warning: Battery is LOW!\n\n")
            if buzzer is not None:
                await buzzer.play("EEE")


async def _check_shutdown_forever(power):
    while True:
        v = await power.should_shut_down()
        if v:
            for _ in range(5):
                await asyncio.sleep(0.1)
                v = await power.should_shut_down()
                if not v:
                    break
            else:
                log.info('Off switch triggered; shutting down...')
                await power.shut_down()
                break
        await asyncio.sleep(1)


async def run_forever():
    controller = CioRoot()
    console = CuiRoot()
    labs = LabsService()

    capabilities = await controller.init()
    await console.init()
    await labs.connect()

    power = None
    buzzer = None

    try:
        if 'Power' in capabilities:
            power = await controller.acquire('Power')
        else:
            log.warning('No power component exists on this device; exiting...')
            return

        if 'Buzzer' in capabilities:
            buzzer = await controller.acquire('Buzzer')
        else:
            pass  # We can tolerate no buzzer.

        log.info('RUNNING!')

        await asyncio.gather(
                _display_forever(power, console, labs, buzzer),
                _check_shutdown_forever(power),
        )

    except asyncio.CancelledError:
        log.info('Battery monitor is being canceled...')

    finally:
        if power is not None:
            await controller.release(power)
            power = None
        if buzzer is not None:
            await controller.release(buzzer)
            buzzer = None
        await controller.close()
        await console.close()
        await labs.close()


if __name__ == '__main__':
    asyncio.run(run_forever())

