###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
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
from auto.services.console.client import CuiRoot

from auto import logger
log = logger.init(__name__, terminal=True)

from auto.services.labs.pty_manager import PtyManager
from auto.services.labs.verification_method import Verification
from auto.services.labs.dashboard import Dashboard
from auto.services.labs.proxy import Proxy

from auto.services.labs.util import set_hostname
from auto.services.labs.settings import save_settings

from auto.services.labs.rpc.server import init as init_rpc_server


WS_BASE_URL = os.environ.get('MAI_WS_URL', 'wss://ws.autoauto.ai/autopair/device')
#WS_BASE_URL = os.environ.get('MAI_WS_URL', 'wss://api.masterai.ai/autopair/device')

PING_INTERVAL_SECONDS = 20


def _log_consumer_error(c):
    log.error('Exception in consumer: {}'.format(type(c).__name__))
    output = io.StringIO()
    traceback.print_exc(file=output)
    log.error(output.getvalue())


def _is_new_device_session(msg):
    if 'origin' in msg and msg['origin'] == 'server':
        if 'connect' in msg and msg['connect'] == 'device':
            vin = msg['vin']
            return vin
    return None


def _is_departed_device_session(msg):
    if 'origin' in msg and msg['origin'] == 'server':
        if 'disconnect' in msg and msg['disconnect'] == 'device':
            vin = msg['vin']
            return vin
    return None


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
            if 'settings' not in info:
                info['settings'] = {}
            settings = info['settings']
            if isinstance(settings, str):
                settings = settings.strip()
            if settings is None or settings == '':
                info['settings'] = {}
            elif isinstance(settings, str):
                info['settings'] = json.loads(settings)
            assert isinstance(info['settings'], dict)
            return info
    return None


class ConnectedSessions:
    def __init__(self, consumers):
        self.consumers = consumers
        self.known_device_sessions = set()
        self.known_usernames = defaultdict(set)
        self.known_user_sessions = set()

    async def add_device_session(self, vin):
        if vin not in self.known_device_sessions:
            self.known_device_sessions.add(vin)

            for c in self.consumers:
                try:
                    await c.new_device_session(vin)
                except:
                    _log_consumer_error(c)

            log.info('Connected device session: {}'.format(vin))

    async def remove_device_session(self, vin):
        if vin in self.known_device_sessions:
            self.known_device_sessions.remove(vin)

            for c in self.consumers:
                try:
                    await c.end_device_session(vin)
                except:
                    _log_consumer_error(c)

            log.info('Departed device session: {}'.format(vin))

    async def close_all_device_sessions(self):
        needs_remove = list(self.known_device_sessions)  # copy

        for vin in needs_remove:
            await self.remove_device_session(vin)

    def has_specific_device_session(self, vin):
        return (vin in self.known_device_sessions)

    def has_any_device_sessions(self):
        return len(self.known_device_sessions) > 0

    async def add_user_session(self, username, user_session):
        if user_session not in self.known_user_sessions:
            self.known_user_sessions.add(user_session)
            self.known_usernames[username].add(user_session)

            for c in self.consumers:
                try:
                    await c.new_user_session(username, user_session)
                except:
                    _log_consumer_error(c)

            log.info('Connected user session: {}: {}'.format(username, user_session))

    async def remove_user_session(self, username, user_session):
        if user_session in self.known_user_sessions:
            self.known_user_sessions.remove(user_session)
            self.known_usernames[username].remove(user_session)

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

    def has_any_user_sessions(self, username=None):
        if username is not None:
            return len(self.known_usernames[username]) > 0
        else:
            return len(self.known_user_sessions) > 0


async def _set_hostname(name):
    output = await set_hostname(name)
    log.info("Set hostname, output is: {}".format(output.strip()))


async def _save_settings(settings, controller):
    did_change = save_settings(settings)
    if did_change:
        log.info("Labs settings were updated, will reboot now.")
        power = await controller.acquire('Power')
        await power.reboot()
        await controller.release(power)
    else:
        log.info("Labs settings did *not* change.")


async def _handle_message(ws, msg, consumers, controller, console, connected_sessions, send_func):
    new_device_vin = _is_new_device_session(msg)
    departed_device_vin = _is_departed_device_session(msg)
    new_user_info = _is_new_user_session(msg)
    departed_user_info = _is_departed_user_session(msg)
    hello_info = _is_hello(msg)

    if new_device_vin is not None:
        await connected_sessions.add_device_session(new_device_vin)

    elif departed_device_vin is not None:
        await connected_sessions.remove_device_session(departed_device_vin)

    elif new_user_info is not None:
        await connected_sessions.add_user_session(*new_user_info)

    elif departed_user_info is not None:
        await connected_sessions.remove_user_session(*departed_user_info)

    elif hello_info is not None:
        vin = hello_info['vin']
        name = hello_info['name']
        description = hello_info['description']  # <-- Where should we display this?
        async def write():
            await console.write_text('Device Name: {}\n'.format(name))
            await console.write_text('Device VIN:  {}\n'.format(vin))
        asyncio.create_task(write())
        asyncio.create_task(_set_hostname(name))
        asyncio.create_task(_save_settings(hello_info['settings'], controller))

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


def _build_send_function(ws, connected_sessions):
    async def smart_send(msg):
        try:
            if isinstance(msg, str):
                msg = json.loads(msg)

            if 'to_vin' in msg:
                # This is a message intended for a peer device.
                to_vin = msg['to_vin']
                if to_vin == 'all':
                    if not connected_sessions.has_any_device_sessions():
                        # No devices are listening.
                        return False
                else:
                    if not connected_sessions.has_specific_device_session(to_vin):
                        # This peer device is not connected right now.
                        return False

            elif 'to_user_session' in msg:
                user_session = msg['to_user_session']
                if not connected_sessions.has_specific_user_session(user_session):
                    # We do not send messages that are destined for a
                    # user session that no longer exists!
                    return False

            elif 'to_username' in msg:
                username = msg['to_username']
                if not connected_sessions.has_any_user_sessions(username):
                    # We don't send to a user who has zero user sessions.
                    return False

            elif 'target' in msg and msg['target'] == 'server':
                # Let this message pass through since it is destined for the server.
                # But remove this flag since it is just for internal libauto usage.
                del msg['target']

            else:
                if not connected_sessions.has_any_user_sessions():
                    # Literally no one is listening, so sending this generic
                    # broadcast message is pointless.
                    return False

            # If we didn't bail out above, then send the message.
            await ws.send(json.dumps(msg))
            return True

        except Exception as e:
            log.error('Exception in `smart_send`: {}'.format(e))
            output = io.StringIO()
            traceback.print_exc(file=output)
            log.error(output.getvalue())
            return False

    return smart_send


async def _run(ws, consumers, controller, console, rpc_interface, publish_func):
    ping_task = asyncio.create_task(_ping_with_interval(ws))

    connected_sessions = ConnectedSessions(consumers)

    send_func = _build_send_function(ws, connected_sessions)

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

            await publish_func('messages', msg)

            start = loop.time()
            await _handle_message(ws, msg, consumers, controller, console, connected_sessions, send_func)
            end = loop.time()

            if end - start > 0.01:
                log.warning('Blocking operation suspected; message receiving loop is being throttled; delay={:.04f}'.format(end - start))
                log.warning('Message was: {}'.format(json.dumps(msg)))

    finally:
        rpc_interface.send_func = None

        await connected_sessions.close_all_device_sessions()
        await connected_sessions.close_all_user_sessions()

        for c in consumers:
            try:
                await c.disconnected_cdp()
            except:
                _log_consumer_error(c)

        ping_task.cancel()
        await ping_task


async def _get_labs_auth_code(controller, console):
    auth = await controller.acquire('Credentials')
    was_missing = False
    while True:
        auth_code = await auth.get_labs_auth_code()
        if auth_code is not None:
            if was_missing:
                await console.write_text("The auth code is now set!\n")
                log.info('The auth code is now set!')
            break
        else:
            if not was_missing:
                await console.write_text("The auth code is not yet set...\n")
                log.info("The auth code is not yet set... will wait...")
                was_missing = True
            await asyncio.sleep(2)
    await controller.release(auth)
    return auth_code


async def init_and_create_forever_task(system_up_user):
    controller = CioRoot()
    console = CuiRoot()

    capabilities = await controller.init()
    await console.init()

    cio_version_iface = await controller.acquire('VersionInfo')
    cio_version = await cio_version_iface.version()
    cio_version = '.'.join([str(v) for v in cio_version])
    cio_name = await cio_version_iface.name()
    await controller.release(cio_version_iface)

    log.info("Libauto version:    {}".format(libauto_version))
    log.info("Controller version: {}".format(cio_version))
    log.info("Controller name:    {}".format(cio_name))

    await console.clear_text()
    await console.big_clear()
    await console.clear_image()
    await console.write_text("Libauto version:    {}\n".format(libauto_version))
    await console.write_text("Controller version: {}\n".format(cio_version))
    await console.write_text("Controller name: {}\n".format(cio_name))

    pubsub_channels = [
        'messages',
    ]

    rpc_server, rpc_interface, publish_func = await init_rpc_server(pubsub_channels)

    consumers = [
        PtyManager(system_up_user, console),
        Verification(console),
        Dashboard(controller, capabilities),
        Proxy(),
    ]

    for c in consumers:
        try:
            await c.init()
        except:
            _log_consumer_error(c)

    await console.write_text('Attempting to connect...\n')

    async def _forever():
        auth_code = await _get_labs_auth_code(controller, console)

        url = WS_BASE_URL + '/' + auth_code

        while True:
            was_connected = False

            try:
                async with ws_connect(url) as ws:
                    log.info("Connected: {}...".format(WS_BASE_URL + '/' + auth_code[:4]))
                    await console.write_text('Connected to Labs. Standing by...\n')
                    was_connected = True
                    await _run(ws, consumers, controller, console, rpc_interface, publish_func)

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

    return asyncio.create_task(_forever())


async def run_forever(system_up_user):
    forever_task = await init_and_create_forever_task(system_up_user)
    await forever_task


if __name__ == '__main__':
    if len(sys.argv) > 1:
        system_up_user = sys.argv[1]   # the "UnPrivileged" system user
    else:
        system_up_user = os.environ['USER']

    asyncio.run(run_forever(system_up_user))

