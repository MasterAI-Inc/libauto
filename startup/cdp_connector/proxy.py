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
        self.connections = {}

    def connected_cdp(self):
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
        asyncio.run_coroutine_threadsafe(self._shutdown_loop(), self.loop)
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

    async def _shutdown_loop(self):
        try:
            read_tasks = []
            writers = []
            for channel, (reader, writer, read_task) in self.connections.items():
                writers.append(writer)
                read_tasks.append(read_task)

            self.connections = {}

            for writer in writers:
                writer.close()
                #await writer.wait_closed()  # <-- Introduced in Python3.7+

            for read_task in read_tasks:
                read_task.cancel()
                await read_task

            self.loop.stop()

        except:
            traceback.print_exc(file=sys.stderr)

    async def _new_message(self, msg, send_func):
        channel = msg['channel']

        try:
            if 'open' in msg:
                port = msg['open']
                try:
                    reader, writer = await asyncio.wait_for(asyncio.open_connection('localhost', port), 1.0)
                    send_func({
                        'type': 'proxy_send',
                        'channel': channel,
                        'data_b85': base64.b85encode(b'==local-connection-success==').decode('ascii'),
                    })
                    read_task = asyncio.ensure_future(self._read(channel, reader, send_func))  # <-- Change `asyncio.ensure_future` to `asyncio.create_task` in Python3.7+.
                    self.connections[channel] = (reader, writer, read_task)
                    log.info('Opened proxy for: {}'.format(channel))
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                    send_func({
                        'type': 'proxy_send',
                        'channel': channel,
                        'data_b85': base64.b85encode(b'==local-connection-failed==').decode('ascii'),
                        'close': True,
                    })

            elif 'close' in msg:
                if channel in self.connections:
                    reader, writer, read_task = self.connections[channel]
                    del self.connections[channel]
                    writer.close()
                    #await writer.wait_closed()  # <-- Introduced in Python3.7+
                    read_task.cancel()
                    await read_task
                    log.info('Closed proxy for: {}'.format(channel))

            else:
                if channel in self.connections:
                    reader, writer, read_task = self.connections[channel]
                    buf = base64.b85decode(msg['data_b85'])
                    if buf != b'':
                        writer.write(buf)
                        await writer.drain()
                    else:
                        writer.write_eof()
                        await writer.drain()

        except:
            traceback.print_exc(file=sys.stderr)

    async def _read(self, channel, reader, send_func):
        # NOTE: The process below is a little simplified. It assumes
        # that we want to close the connection as soon as we see EOF on
        # the reader. This isn't strictly correct. It's possible a TCP
        # connection can write EOF but still expect to read data. We
        # should revisit this in the future. For now, it works for all
        # the application-layer protocols we care about (i.e. HTTP/Websockets).

        try:
            while True:
                buf = await reader.read(4096)
                extra = {'close': True} if buf == b'' else {}
                send_func({
                    'type': 'proxy_send',
                    'channel': channel,
                    'data_b85': base64.b85encode(buf).decode('ascii'),
                    **extra
                })
                if buf == b'':
                    log.info("Read task ending: {}".format(channel))
                    break

        except asyncio.CancelledError:
            log.info("Read task canceled: {}".format(channel))

        except:
            traceback.print_exc(file=sys.stderr)

