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

from cui.mock_impl import CuiMock


if __name__ == '__main__':
    c = CuiMock()
    c.init()

    # Put up a big full-screen image by passing an image-path.
    c.big_image('wifi_success')
    time.sleep(2)

    # Put up some big text!
    for i in range(1, 5):
        text = "All is good... {}".format(i)
        c.big_status(text)
        time.sleep(1)

    # Clear the big text.
    c.big_status('')
    time.sleep(2)

    # Clear the screen of the big image and text.
    c.big_clear()
    time.sleep(2)

