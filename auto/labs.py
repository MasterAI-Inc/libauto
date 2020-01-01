###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
Module to interface with your AutoAuto Labs account.

This is a **synchronous** interface.
"""

import os
import time
import json

import rpyc
CONN = rpyc.connect("localhost", 18864, config={'sync_request_timeout': 30})


def send_message_to_labs(msg):
    """
    Send a message to your Labs account.
    """
    to_user_session = os.environ.get('TO_USER_SESSION', None)
    to_username     = os.environ.get('TO_USERNAME', None)
    if to_user_session:
        msg['to_user_session'] = to_user_session
    elif to_username:
        msg['to_username'] = to_username
    did_send = CONN.root.send(json.dumps(msg))
    time.sleep(0.1)  # Throttle messages to the CDP. Please be nice to our servers, else your account will be suspended.
    return did_send

