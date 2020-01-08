###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
#
###############################################################################

"""
This module provides an RPC service which listens and communicates through a
websockets server.
"""

import asyncio
import websockets
import uuid

from auto.rpc.packer import pack, unpack
from auto.rpc.serialize_interface import serialize_interface


class SerializeIface(Exception):
    """
    Raise this exception from your exposed service to cause a sub-interface
    to be serialized and sent to the client. This is useful when you cannot
    serialize the full interface from the beginning, and you must instead
    serialize part of the interface at runtime.
    """
    def __init__(self, obj, whitelist_method_names=()):
        self.obj = obj
        self.whitelist_method_names = whitelist_method_names


async def serve(root_factory, pubsub=None, inet_addr='localhost', inet_port=7000):
    """
    Serve an RPC server for objects created by `root_factory`. Each new client will
    receive its own copy of the root object as created by the `root_factory`. Clients
    may also subscribe to events which appear in the `pubsub` list of available
    catalogs. The websockets server will listen on the given `inet_addr` and `inet_port`.

    The `root_factory` may return a tuple of `(root, whitelist_method_names)` if it
    so chooses; otherwise it is assumed it only returns the `root` instance and does
    not specify `whitelist_method_names`. Also, the `root_factory` might return the same
    object on each invocation; that is the choice of the `root_factory`.
    """
    subscribers = {}

    handle_client = _build_client_handler(root_factory, pubsub, subscribers)

    start_server = websockets.serve(handle_client, inet_addr, inet_port)

    server = await start_server

    async def publish_func(channel, payload):
        client_list = subscribers.get(channel, [])
        if client_list:
            message = {
                'type': 'publish',
                'channel': channel,
                'payload': payload,
            }
            message_buf = pack(message)
            tasks = []
            for client in client_list:
                task = asyncio.create_task(client.send(message_buf))
                tasks.append(task)
            await asyncio.wait(tasks)

    return server, publish_func


def _build_client_handler(root_factory, pubsub, subscribers):
    channels = pubsub['channels'] if pubsub is not None else []
    channels_buf = pack(channels)

    async def handle_client(ws, path):
        root = root_factory()
        whitelist_method_names = ()
        if isinstance(root, tuple):
            root, whitelist_method_names = root
        iface, impl = serialize_interface(root, name='root', whitelist_method_names=whitelist_method_names)
        iface_buf = pack(iface)
        await ws.send(iface_buf)
        await ws.send(channels_buf)
        return await _handle_client(root, ws, impl, pubsub, subscribers)

    return handle_client


async def _safe_invoke(func, *args):
    if asyncio.iscoroutinefunction(func):
        return await func(*args)
    else:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, func, *args)


async def _handle_client(root, ws, impl, pubsub, subscribers):
    setup = getattr(root, 'setup', None)
    if setup is not None:
        await _safe_invoke(setup, ws)

    try:
        while True:
            cmd = await ws.recv()
            cmd = unpack(cmd)
            type_ = cmd['type']

            if type_ == 'invoke':
                asyncio.create_task(_handle_client_invoke(ws, cmd, impl))

            elif type_ == 'subscribe':
                await _handle_client_subscribe(ws, cmd, pubsub, subscribers)

            elif type_ == 'unsubscribe':
                await _handle_client_unsubscribe(ws, cmd, pubsub, subscribers)

    except websockets.exceptions.ConnectionClosed:
        pass   # We consider this normal; fall through.

    await _handle_client_unsubscribe_all(ws, pubsub, subscribers)

    cleanup = getattr(root, 'cleanup', None)
    if cleanup is not None:
        await _safe_invoke(cleanup)


async def _handle_client_invoke(ws, cmd, impl):
    id_ = cmd['id']
    path = cmd['path']
    args = cmd['args']
    func = impl[path]

    result = {
        'type': 'invoke_result',
        'id': id_,
    }

    try:
        val = await _safe_invoke(func, *args)
        result['val'] = val

    except SerializeIface as s:
        sub_obj = s.obj
        sub_whitelist = s.whitelist_method_names
        sub_name = path + '.' + str(uuid.uuid4())
        sub_iface, sub_impl = serialize_interface(sub_obj, name=sub_name, whitelist_method_names=sub_whitelist)
        impl.update(sub_impl)
        result['iface'] = sub_iface

    except Exception as e:
        result['exception'] = str(e)   # TODO: Serialize the exception more fully so it can be stacktraced on the other side.

    result_buf = pack(result)
    await ws.send(result_buf)


async def _handle_client_subscribe(ws, cmd, pubsub, subscribers):
    channel = cmd['channel']

    if (pubsub is None) or (channel not in pubsub['channels']):
        return   # TODO: send an error to the client so they know they messed up.

    if channel not in subscribers:
        subscribers[channel] = set()

    if ws not in subscribers[channel]:
        subscribers[channel].add(ws)

        sub_callback = pubsub['subscribe']
        if sub_callback is not None:
            await _safe_invoke(sub_callback, channel)


async def _handle_client_unsubscribe(ws, cmd, pubsub, subscribers):
    channel = cmd['channel']

    if (pubsub is None) or (channel not in pubsub['channels']):
        return   # TODO: send an error to the client so they know they messed up.

    if (channel in subscribers) and (ws in subscribers[channel]):
        subscribers[channel].remove(ws)

        if len(subscribers[channel]) == 0:
            del subscribers[channel]

        unsub_callback = pubsub['unsubscribe']
        if unsub_callback is not None:
            await _safe_invoke(unsub_callback, channel)


async def _handle_client_unsubscribe_all(ws, pubsub, subscribers):
    if pubsub is None:
        return

    unsub_callback = pubsub['unsubscribe']

    channels = [c for c, ws_set in subscribers.items() if ws in ws_set]

    for c in channels:
        subscribers[c].remove(ws)
        if len(subscribers[c]) == 0:
            del subscribers[c]

    if unsub_callback is not None:
        for c in channels:
            await _safe_invoke(unsub_callback, c)


async def _demo():
    class Thing:
        async def setup(self, ws):
            # This method is optional, but if implemented it will
            # be invoked for each new client.
            self.ws = ws
            print('NEW CONNECTION:', self.ws.remote_address)

        async def export_foo(self, x):
            print('I am foo.')
            return x ** 3

        async def cleanup(self):
            # This method is optional, but if implemented it will
            # be invoked once the client disconnects.
            print('DEAD CONNECTION:', self.ws.remote_address)

    pubsub = {
        'channels': [
            'ping',
        ],
        'subscribe': None,
        'unsubscribe': None,
    }

    server, publish_func = await serve(Thing, pubsub)

    for i in range(1, 1000000):
        await publish_func('ping', f'Ping #{i}')
        await asyncio.sleep(1)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_demo())

