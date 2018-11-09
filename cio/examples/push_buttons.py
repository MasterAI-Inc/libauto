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
from pprint import pprint
from cio import default_handle as h

pprint(h.CAPS)

b = h.acquire_component_interface('PushButtons')

n = b.num_buttons()

print(n)

# for i in range(1000):
#     print(b.debug())
#     time.sleep(0.1)

states = [b.button_state(i) for i in range(n)]

while True:

    for prev_state, i in zip(states, range(n)):
        state = b.button_state(i)
        if state == prev_state:
            continue

        diff_presses  = (state[0] - prev_state[0]) % 256
        diff_releases = (state[1] - prev_state[1]) % 256

        if diff_presses > 0:
            print("Button #{} pressed {} time{}".format(i+1, diff_presses, 's' if diff_presses > 1 else ''))
        if diff_releases > 0:
            print("Button #{} released {} time{}".format(i+1, diff_releases, 's' if diff_releases > 1 else ''))

        states[i] = state

    time.sleep(0.05)

