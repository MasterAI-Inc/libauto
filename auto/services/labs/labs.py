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
from websockets import connect as ws_connect
from websockets import WebSocketException

from auto import __version__ as libauto_version

from auto.services.controller.client import CioRoot
from auto.services.camera.client import CameraRGB
from auto.services.console.client import CuiRoot

from auto import logger
log = logger.init('labs connection', terminal=True)

from pty_manager import PtyManager
from verification_method import Verification
from dashboard import Dashboard
from proxy import Proxy


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


def _add_user_session(username, user_session):
    with self.known_lock:
        if user_session not in self.known_user_sessions:
            self.known_user_sessions.add(user_session)
            self.known_usernames[username].add(user_session)
            return True
        return False


def _remove_user_session(username, user_session):
    with self.known_lock:
        if user_session in self.known_user_sessions:
            self.known_user_sessions.remove(user_session)
            self.known_usernames[username].remove(user_session)
            return True
        return False


async def _set_hostname(name):
    pass  # TODO


async def _handle_message(ws, msg, consumers, console):
    new_user_info = _is_new_user_session(msg)
    departed_user_info = _is_departed_user_session(msg)
    hello_info = _is_hello(msg)

    if new_user_info is not None:
        if _add_user_session(*new_user_info):
            for c in consumers:
                try:
                    await c.new_user_session(*new_user_info)
                except:
                    _log_consumer_error(c)

    elif departed_user_info is not None:
        if _remove_user_session(*departed_user_info):
            for c in consumers:
                try:
                    await c.end_user_session(*departed_user_info)
                except:
                    _log_consumer_error(c)

    elif hello_info is not None:
        vin = hello_info['vin']
        name = hello_info['name']
        description = hello_info['description']  # <-- Where should we display this?
        await console.write_text('Device Name: {}\n'.format(name))
        await console.write_text('Device VIN:  {}\n'.format(vin))
        output = await _set_hostname(name)
        log.info("Set hostname, output is: {}".format(output))

    else:
        for c in consumers:
            try:
                await c.got_message(msg, self.smart_send)   # TODO
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


async def _run(ws, consumers, console):
    ping_task = asyncio.create_task(_ping_with_interval(ws))

    for c in consumers:
        try:
            await c.connected_cdp()
        except:
            _log_consumer_error(c)

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

            await _handle_message(ws, msg, consumers, console)

    finally:
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
    await console.write_text("Libauto version:    {}\n".format(libauto_version))
    await console.write_text("Controller version: {}\n".format(cio_version))

    token = await _get_token(controller, console)

    url = BASE_URL + '/' + token

    consumers = [
        #PtyManager(system_up_user, console),
        Verification(console),
        #Dashboard(camera, controller),
        #Proxy(),
    ]

    await console.write_text('Attempting to connect...\n')

    while True:
        was_connected = False

        try:
            async with ws_connect(url) as ws:
                log.info("Connected: {}...".format(BASE_URL + '/' + token[:4]))
                await console.write_text('Connected to CDP. Standing by...\n')
                was_connected = True
                await _run(ws, consumers, console)

        except WebSocketException as e:
            log.info('Connection closed: {}'.format(e))
            if was_connected:
                await console.write_text('Connection to CDP lost. Reconnecting...\n')

        except Exception as e:
            log.error('Unknown error: {}'.format(e))

        finally:
            reconnect_delay_seconds = 10 + random.randint(2, 8)
            await asyncio.sleep(reconnect_delay_seconds)


if __name__ == '__main__':
    system_up_user = sys.argv[1]   # the "UnPrivileged" system user

    asyncio.run(run_forever(system_up_user))

