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
This is a simple process which monitors the buttons on the device and activates
the calibration script when the _first_ and _last_ buttons are pressed for
six consecutive seconds.
"""

import asyncio

from auto.services.controller.client import CioRoot

from auto import logger
log = logger.init(__name__, terminal=True)


async def _run_calibration(calibrator, buzzer):
    log.info('Starting calibration sequence!')
    await buzzer.play()
    script_name = await calibrator.script_name()
    proc = await asyncio.create_subprocess_exec(script_name)
    await proc.communicate()
    log.info('Calibration ended.')


async def _monitor(buttons, calibrator, buzzer):
    n_buttons = await buttons.num_buttons()
    button_indices = [0, n_buttons-1]  # the _first_ and _last_ buttons

    count = 0

    while True:
        for b in button_indices:
            num_presses, num_releases, is_currently_pressed = await buttons.button_state(b)
            if not is_currently_pressed:
                count = 0
                break
        else:
            # All buttons are currently pressed.
            count += 1
            if count == 12:
                await _run_calibration(calibrator, buzzer)
                count = 0
        await asyncio.sleep(0.5)


async def run_forever():
    controller = CioRoot()

    capabilities = await controller.init()

    buttons = None
    calibrator = None
    buzzer = None

    try:
        if 'PushButtons' in capabilities:
            buttons = await controller.acquire('PushButtons')
        else:
            log.warning('No push buttons exists on this device; exiting...')
            return

        if 'Calibrator' in capabilities:
            calibrator = await controller.acquire('Calibrator')
        else:
            log.warning('No calibrator exists on this device; exiting...')
            return

        if 'Buzzer' in capabilities:
            buzzer = await controller.acquire('Buzzer')
        else:
            pass  # We can tolerate no buzzer.

        log.info('RUNNING!')

        await _monitor(buttons, calibrator, buzzer)

    except asyncio.CancelledError:
        log.info('Calibration monitor is being canceled...')

    finally:
        if buttons is not None:
            await controller.release(buttons)
            buttons = None
        if calibrator is not None:
            await controller.release(calibrator)
            calibrator = None
        if buzzer is not None:
            await controller.release(buzzer)
            buzzer = None
        await controller.close()


if __name__ == '__main__':
    asyncio.run(run_forever())

