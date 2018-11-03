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
import re
from auto import print_all
from auto import console


class Verification:

    def __init__(self):
        pass

    def connected_cdp(self):
        pass

    def new_user_session(self, username, user_session):
        pass

    def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'server':
            if 'verification_text' in msg:
                self._show_verification_text(msg['username'], msg['verification_text'], msg['expire_minutes'])
            elif 'verification_success' in msg:
                if msg['verification_success']:
                    self._show_verification_success(msg['username'])
                else:
                    self._show_verification_failed(msg['reason'])

    def end_user_session(self, username, user_session):
        pass

    def disconnected_cdp(self):
        pass

    def _show_verification_text(self, username, verification_text, expire_minutes):
        text = "Hi {}!\nAuthentication Code: {}".format(username, verification_text)
        console.big_image('images/pair_pending.png')
        console.big_status(text)
        print_all(text + "\n")
        # TODO Use the `expire_minutes`. E.g. Put a countdown on the screen
        # and auto-close the pairing image when the countdown expires.

    def _show_verification_success(self, username):
        text = "Congrats {}!\nYou are paired with this device.".format(username)
        console.big_image('images/pair_success.png')
        console.big_status(text)
        print_all(text + "\n")
        time.sleep(5)   # <-- TODO Remove this hack. Do something that's async.
        console.big_clear()

    def _show_verification_failed(self, reason):
        reason = re.sub(r'\<.*?\>', '', reason)
        text = "Error:\n{}".format(reason)
        console.big_image('images/pair_error.png')
        console.big_status("Error:\nTry again.")
        print_all(text + "\n")
        time.sleep(5)   # <-- TODO Remove this hack. Do something that's async.
        console.big_clear()

