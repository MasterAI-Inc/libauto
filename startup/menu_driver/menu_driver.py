###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import time

from collections import deque

from auto.capabilities import list_caps, acquire, release

from auto import logger
log = logger.init('battery_monitor', terminal=True)


log.info("Starting menu driver process...")


buttons = acquire("PushButtons")

button_stream = deque()

combo = [1, 1, 2, 1, 3, 1]


def _run_menu():
    # TODO: This should, someday, be a nice menu of options shown on the LCD screen.
    #       For now, however, we'll just run the calibration routine.
    #       In the future, the calibration routine will be _one_ of the menu options.
    from car.calibration import calibrate
    calibrate('car')   # <-- blocks until calibration is finished


while True:

    events = buttons.get_events()
    presses = [e['button'] for e in events if e['action'] == 'pressed']
    if presses:
        button_stream.extend(presses)
        while len(button_stream) > len(combo):
            button_stream.popleft()
        if list(button_stream) == combo:
            log.info("Menu button combination was entered! Will open menu...")
            release(buttons)
            _run_menu()
            buttons = acquire('PushButtons')
            log.info("Menu closed.")

    time.sleep(1.0)

