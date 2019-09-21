###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

import os
import uuid
import base64
import subprocess
from queue import Queue, Empty
from threading import Thread

import auto
from auto.camera_rpc_client import CameraRGB
from auto.camera import wrap_frame_index_decorator, base64_encode_image
from auto.inet import Wireless, list_wifi_ifaces, get_ip_address
from cio.rpc_client import VERSION as cio_version

from auto import logger
log = logger.init(__name__, terminal=True)


RESPONSE = '\r\n'.join('''HTTP/1.1 200 OK
Content-Length: 4
Content-Type: text/html

Hi!!'''.splitlines()).encode('ascii')


class Proxy:

    def __init__(self):
        pass

    def connected_cdp(self):
        pass

    def new_user_session(self, username, user_session):
        pass

    def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'proxy':
            print(msg)
            if 'open' in msg:
                send_func({
                    'type': 'proxy_send',
                    'channel': msg['channel'],
                    'data_b85': base64.b85encode(b'==local-connection-success==').decode('ascii'),
                    #'close': True,
                })
            else:
                if 'data_b85' in msg and msg['data_b85']:
                    send_func({
                        'type': 'proxy_send',
                        'channel': msg['channel'],
                        'data_b85': base64.b85encode(RESPONSE).decode('ascii'),
                        #'close': True,
                    })
                else:
                    send_func({
                        'type': 'proxy_send',
                        'channel': msg['channel'],
                        'data_b85': '',
                        'close': True,
                    })

    def end_user_session(self, username, user_session):
        pass

    def disconnected_cdp(self):
        pass

