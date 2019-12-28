###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import sys
import time

from cui.pygame_impl import CuiPyGame


if __name__ == '__main__':
    c = CuiPyGame()
    c.init()

    while True:
        try:
            text = sys.stdin.readline()
        except KeyboardInterrupt:
            c.clear_text()
            break

        c.write_text(text)

    time.sleep(3)

