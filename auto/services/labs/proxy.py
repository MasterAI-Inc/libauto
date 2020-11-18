###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

import sys
import base64
import asyncio
import traceback

from auto import logger
log = logger.init(__name__, terminal=True)


READ_BUF_SIZE = 4096*8


class Proxy:

    def __init__(self):
        pass

    async def init(self):
        pass

    async def connected_cdp(self):
        self.connections = {}   # maps channel to task

    async def new_device_session(self, vin):
        pass

    async def new_user_session(self, username, user_session):
        pass

    async def got_message(self, msg, send_func):
        if 'origin' in msg and msg['origin'] == 'proxy':
            channel = msg['channel']

            if 'open' in msg:
                if channel in self.connections:
                    log.error('{}: Request to open an already open connection.'.format(channel))
                    return
                queue = asyncio.Queue()
                queue.put_nowait(msg)
                task = asyncio.create_task(_manage_connection(channel, queue, send_func))
                self.connections[channel] = (task, queue)

            elif 'close' in msg:
                if channel not in self.connections:
                    log.error('{}: Request to close an unknown connection.'.format(channel))
                    return
                task, queue = self.connections[channel]
                del self.connections[channel]
                task.cancel()

            else:
                if channel not in self.connections:
                    log.error('{}: Request to write to an unknown connection.'.format(channel))
                    return
                task, queue = self.connections[channel]
                queue.put_nowait(msg)

    async def end_device_session(self, vin):
        pass

    async def end_user_session(self, username, user_session):
        pass

    async def disconnected_cdp(self):
        for channel, (task, queue) in self.connections.items():
            task.cancel()
        self.connections = {}


async def _manage_connection(channel, queue, send_func):
    reader = None
    writer = None
    read_task = None

    n_read_bytes = 0
    n_write_bytes = 0

    try:
        while True:
            msg = await queue.get()

            if 'open' in msg:
                port = msg['open']
                try:
                    reader, writer = await asyncio.wait_for(asyncio.open_connection('127.0.0.1', port), 1.0)
                    await send_func({
                        'type': 'proxy_send',
                        'channel': channel,
                        'data_b85': base64.b85encode(b'==local-connection-success==').decode('ascii'),
                        'target': 'server',
                    })
                except (asyncio.TimeoutError, ConnectionRefusedError, OSError) as e:
                    await send_func({
                        'type': 'proxy_send',
                        'channel': channel,
                        'data_b85': base64.b85encode(b'==local-connection-failed==').decode('ascii'),
                        'close': True,
                        'target': 'server',
                    })
                    log.info('{}: Connection to port {} failed with error: {}'.format(channel, port, str(e)))
                    return
                read_task = asyncio.create_task(_read(channel, reader, send_func))
                log.info('{}: Opened connection.'.format(channel))

            else:
                buf = base64.b85decode(msg['data_b85'])
                if buf != b'':
                    writer.write(buf)
                else:
                    writer.write_eof()
                await writer.drain()
                n_write_bytes += len(buf)

    except asyncio.CancelledError:
        log.info('{}: Connection told to cancel/close.'.format(channel))

    except:
        log.error('{}: Unknown exception in in connection manager.'.format(channel))
        traceback.print_exc(file=sys.stderr)

    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()
            log.info('{}: Writer closed.'.format(channel))

        if read_task is not None:
            read_task.cancel()
            n_read_bytes = await read_task
            log.info('{}: Read task canceled.'.format(channel))

    log.info('{}: total bytes read: {} ; total bytes written: {}'.format(channel, n_read_bytes, n_write_bytes))


async def _read(channel, reader, send_func):
    # NOTE: The process below is a little simplified. It assumes
    # that we want to close the connection as soon as we see EOF on
    # the reader. This isn't strictly correct. It's possible a TCP
    # connection can write EOF but still expect to read data. We
    # should revisit this in the future. For now, it works for all
    # the application-layer protocols we care about (i.e. HTTP/Websockets).

    n_read_bytes = 0

    try:
        while True:
            buf = await reader.read(READ_BUF_SIZE)
            n_read_bytes += len(buf)
            extra = {'close': True} if buf == b'' else {}
            await send_func({
                'type': 'proxy_send',
                'channel': channel,
                'data_b85': base64.b85encode(buf).decode('ascii'),
                'target': 'server',
                **extra
            })
            if buf == b'':
                log.info('{}: Read task saw EOF.'.format(channel))
                break

    except asyncio.CancelledError:
        log.info('{}: Read task told to cancel.'.format(channel))

    except:
        log.error('{}: Unknown exception in in reader.'.format(channel))
        traceback.print_exc(file=sys.stderr)

    return n_read_bytes

