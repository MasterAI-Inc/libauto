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
import base64
import asyncio
import traceback
from threading import Thread

from auto import logger
log = logger.init(__name__, terminal=True)


class Proxy:

    def __init__(self):
        pass

    def connected_cdp(self):
        self.connections = {}
        self.loop = asyncio.new_event_loop()
        self.thread = Thread(target=self._run_event_loop)
        self.thread.start()
        log.info("Started proxy thread.")

    def new_user_session(self, username, user_session):
        pass

    def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'proxy':
            asyncio.run_coroutine_threadsafe(self._new_message(msg, send_func), self.loop)

    def end_user_session(self, username, user_session):
        pass

    def disconnected_cdp(self):
        log.info("Will stop proxy event loop...")
        self.loop.call_soon_threadsafe(self.loop.stop)
        log.info("Will join with proxy thread...")
        self.thread.join()
        self.loop = None
        self.thread = None
        log.info("Joined proxy thread!")

    def _run_event_loop(self):
        asyncio.set_event_loop(self.loop)
        log.info("Proxy event loop will start!")
        self.loop.run_forever()
        self.loop.close()
        log.info("Proxy event loop has stopped.")
        # TODO clean up open connections

    async def _new_message(self, msg, send_func):
        print(msg)
        try:
            if 'open' in msg:
                port = msg['open']
                try:
                    reader, writer = await asyncio.wait_for(asyncio.open_connection('localhost', port), 1.0)
                    send_func({
                        'type': 'proxy_send',
                        'channel': msg['channel'],
                        'data_b85': base64.b85encode(b'==local-connection-success==').decode('ascii'),
                        #'close': True,
                    })
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                    send_func({
                        'type': 'proxy_send',
                        'channel': msg['channel'],
                        'data_b85': base64.b85encode(b'==local-connection-failed==').decode('ascii'),
                        'close': True,
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
        except:
            traceback.print_exc(file=sys.stderr)

