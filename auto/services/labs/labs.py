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
import io
import sys
import json
import random
import asyncio
import traceback
from collections import defaultdict
from websockets import connect as ws_connect
from websockets import WebSocketException

from auto import __version__ as libauto_version

from auto.services.controller.client import CioRoot
from auto.services.camera.client import CameraRGB
from auto.services.console.client import CuiRoot

from auto import logger
log = logger.init(__name__, terminal=True)

from auto.services.labs.pty_manager import PtyManager
from auto.services.labs.verification_method import Verification
from auto.services.labs.dashboard import Dashboard
from auto.services.labs.proxy import Proxy

from auto.services.labs.util import set_hostname

from auto.services.labs.rpc.server import init as init_rpc_server


BASE_PROTO = os.environ.get('LABS_PROTO', 'wss')
BASE_HOST  = os.environ.get('LABS_HOST', 'ws.autoauto.ai')
BASE_URL = "{}://{}/autopair/device".format(BASE_PROTO, BASE_HOST)

PING_INTERVAL_SECONDS = 20


def _log_consumer_error(c):
    log.error('Exception in consumer: {}'.format(type(c).__name__))
    output = io.StringIO()
    traceback.print_exc(file=output)
    log.error(output.getvalue())


def _is_new_user_session(msg):
    if 'origin' in msg and msg['origin'] == 'server':
        if 'connect' in msg and msg['connect'] == 'user':
            username = msg['username']
            user_session = msg['user_session']
            return username, user_session
    return None


def _is_departed_user_session(msg):
    if 'origin' in msg and msg['origin'] == 'server':
        if 'disconnect' in msg and msg['disconnect'] == 'user':
            username = msg['username']
            user_session = msg['user_session']
            return username, user_session
    return None


def _is_hello(msg):
    if 'origin' in msg and msg['origin'] == 'server':
        if 'hello' in msg:
            info = msg['yourinfo']
            return info
    return None


class ConnectedUserSessions:
    def __init__(self, consumers):
        self.consumers = consumers
        self.known_usernames = defaultdict(set)
        self.known_user_sessions = set()

    async def add_user_session(self, username, user_session):
        did_add = False

        if user_session not in self.known_user_sessions:
            self.known_user_sessions.add(user_session)
            self.known_usernames[username].add(user_session)
            did_add = True

        if did_add:
            for c in self.consumers:
                try:
                    await c.new_user_session(username, user_session)
                except:
                    _log_consumer_error(c)
            log.info('Connected user session: {}: {}'.format(username, user_session))

    async def remove_user_session(self, username, user_session):
        did_remove = False

        if user_session in self.known_user_sessions:
            self.known_user_sessions.remove(user_session)
            self.known_usernames[username].remove(user_session)
            did_remove = True

        if did_remove:
            for c in self.consumers:
                try:
                    await c.end_user_session(username, user_session)
                except:
                    _log_consumer_error(c)
            log.info('Departed user session: {}: {}'.format(username, user_session))

    async def close_all_user_sessions(self):
        needs_remove = []

        for username, user_session_set in self.known_usernames.items():
            for user_session in user_session_set:
                needs_remove.append((username, user_session))

        for username, user_session in needs_remove:
            await self.remove_user_session(username, user_session)

    def has_specific_user_session(self, user_session):
        return user_session in self.known_user_sessions

    def has_any_user_sessions(self, username):
        return len(self.known_usernames[username]) > 0

    def has_any_sessions(self):
        return len(self.known_user_sessions) > 0


async def _set_hostname(name):
    output = await set_hostname(name)
    log.info("Set hostname, output is: {}".format(output.strip()))


async def _handle_message(ws, msg, consumers, console, connected_user_sessions, send_func):
    new_user_info = _is_new_user_session(msg)
    departed_user_info = _is_departed_user_session(msg)
    hello_info = _is_hello(msg)

    if new_user_info is not None:
        await connected_user_sessions.add_user_session(*new_user_info)

    elif departed_user_info is not None:
        await connected_user_sessions.remove_user_session(*departed_user_info)

    elif hello_info is not None:
        vin = hello_info['vin']
        name = hello_info['name']
        description = hello_info['description']  # <-- Where should we display this?
        async def write():
            await console.write_text('Device Name: {}\n'.format(name))
            await console.write_text('Device VIN:  {}\n'.format(vin))
        asyncio.create_task(write())
        asyncio.create_task(_set_hostname(name))

    else:
        for c in consumers:
            try:
                await c.got_message(msg, send_func)
            except:
                _log_consumer_error(c)


async def _ping_with_interval(ws):
    try:
        log.info('Ping task started.')
        while True:
            await asyncio.sleep(PING_INTERVAL_SECONDS)
            await ws.send(json.dumps({'ping': True}))
            log.info('Sent ping to server.')
    except asyncio.CancelledError:
        log.info('Ping task is terminating.')


def _build_send_function(ws, connected_user_sessions):
    async def smart_send(msg):
        try:
            if isinstance(msg, str):
                msg = json.loads(msg)

            if 'to_user_session' in msg:
                user_session = msg['to_user_session']
                if not connected_user_sessions.has_specific_user_session(user_session):
                    # We do not send messages that are destined for a
                    # user session that no longer exists!
                    return False

            elif 'to_username' in msg:
                username = msg['to_username']
                if not connected_user_sessions.has_any_user_sessions(username):
                    # We don't send to a user who has zero user sessions.
                    return False

            elif 'type' in msg and msg['type'] == 'proxy_send':
                # Special case. The proxy should still work if there are no
                # user sessions (because a user can use the proxy without the
                # normal "session" existing).
                pass

            else:
                if not connected_user_sessions.has_any_sessions():
                    # Literally no one is listening, so sending this generic
                    # broadcast message is pointless.
                    return False

            # If we didn't bail out above, then send the message.
            await ws.send(json.dumps(msg))
            return True

        except Exception as e:
            log.error('Exception in `smart_send`: {}'.format(e))
            return False

    return smart_send


async def _run(ws, consumers, console, rpc_interface):
    ping_task = asyncio.create_task(_ping_with_interval(ws))

    connected_user_sessions = ConnectedUserSessions(consumers)

    send_func = _build_send_function(ws, connected_user_sessions)

    loop = asyncio.get_running_loop()

    for c in consumers:
        try:
            await c.connected_cdp()
        except:
            _log_consumer_error(c)

    rpc_interface.send_func = send_func

    try:
        while True:
            msg = await ws.recv()

            try:
                msg = json.loads(msg)
            except json.JSONDecodeError:
                log.error('Got bad JSON message: {}'.format(repr(msg)))
                continue

            if 'ping' in msg:
                log.info('Got ping from server; will send pong back.')
                await ws.send(json.dumps({'pong': True}))
                continue

            if 'pong' in msg:
                log.info('Got pong from server!')
                continue

            start = loop.time()
            await _handle_message(ws, msg, consumers, console, connected_user_sessions, send_func)
            end = loop.time()

            if end - start > 0.01:
                log.warning('Blocking operation suspected; message receiving loop is being throttled; delay={:.04f}'.format(end - start))
                log.warning('Message was: {}'.format(json.dumps(msg)))

    finally:
        rpc_interface.send_func = None

        await connected_user_sessions.close_all_user_sessions()

        for c in consumers:
            try:
                await c.disconnected_cdp()
            except:
                _log_consumer_error(c)

        ping_task.cancel()
        await ping_task


async def _get_token(controller, console):
    auth = await controller.acquire('Credentials')
    was_missing = False
    while True:
        token = await auth.get_token()
        if token:
            if was_missing:
                await console.write_text("The token is now set!\n")
                log.info('The token is now set!')
            break
        else:
            if not was_missing:
                await console.write_text("Token not yet set...\n")
                log.info("Token not yet set... will wait...")
                was_missing = True
            await asyncio.sleep(2)
    await controller.release(auth)
    return token


async def run_forever(system_up_user):
    controller = CioRoot()
    camera = CameraRGB()
    console = CuiRoot()

    await controller.init()
    await camera.connect()
    await console.init()

    cio_version_iface = await controller.acquire('VersionInfo')
    cio_version = await cio_version_iface.version()
    cio_version = '.'.join([str(v) for v in cio_version])
    await controller.release(cio_version_iface)

    log.info("Libauto version:    {}".format(libauto_version))
    log.info("Controller version: {}".format(cio_version))

    await console.clear_text()
    await console.big_clear()
    await console.clear_image()
    await console.write_text("Libauto version:    {}\n".format(libauto_version))
    await console.write_text("Controller version: {}\n".format(cio_version))

    token = await _get_token(controller, console)

    url = BASE_URL + '/' + token

    rpc_server, rpc_interface = await init_rpc_server()

    consumers = [
        PtyManager(system_up_user, console),
        Verification(console),
        Dashboard(camera, controller),
        Proxy(),
    ]

    for c in consumers:
        try:
            await c.init()
        except:
            _log_consumer_error(c)

    await console.write_text('Attempting to connect...\n')

    while True:
        was_connected = False

        try:
            async with ws_connect(url) as ws:
                log.info("Connected: {}...".format(BASE_URL + '/' + token[:4]))
                await console.write_text('Connected to Labs. Standing by...\n')
                was_connected = True
                await _run(ws, consumers, console, rpc_interface)

        except WebSocketException as e:
            log.info('Connection closed: {}'.format(e))
            if was_connected:
                await console.write_text('Connection to Labs was lost.\nReconnecting...\n')

        except Exception as e:
            log.error('Unknown error: {}'.format(e))

        finally:
            reconnect_delay_seconds = 10 + random.randint(2, 8)
            log.info('Waiting {} seconds before reconnecting.'.format(reconnect_delay_seconds))
            await asyncio.sleep(reconnect_delay_seconds)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        system_up_user = sys.argv[1]   # the "UnPrivileged" system user
    else:
        system_up_user = os.environ['USER']

    asyncio.run(run_forever(system_up_user))

