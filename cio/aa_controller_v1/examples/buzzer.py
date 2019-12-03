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

b = h.acquire_component_interface('Buzzer')

time.sleep(2)

#b.play()                   # defaults to the 'on' sound
#b.play('o4l16ceg>c8')      # the 'on' sound (explicit this time)
#b.play('v10>>g16>>>c16')   # the soft reset sound
#b.play('>E>E>E R >C>E>G')
#b.play('!L16 V12 cdefgab>cbagfedc')   # C-major scale up and down
b.play('!T240 L8 agafaea dac+adaea fa<aa<bac#a dac#adaea f4')   # "Bach's fugue in D-minor"

time.sleep(5)

