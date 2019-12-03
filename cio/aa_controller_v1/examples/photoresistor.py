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
from cio.aa_controller_v1 import default_handle as h

pprint(h.CAPS)

p = h.acquire_component_interface('Photoresistor')

for i in range(1000):
    print(p.read(), p.read_millivolts(), p.read_ohms())
    time.sleep(0.1)

