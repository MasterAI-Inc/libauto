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

while True:

    events = b.get_events()

    for e in events:
        pprint(e)

    time.sleep(0.5)

