import asyncio
import websockets
import json

from auto.rpc.serialize_interface import serialize_interface


async def serve(root, inet_addr='localhost', inet_port=7000):
    iface, impl = serialize_interface(root, name='root')

    handle_client = _build_server_func(iface, impl)

    start_server = websockets.serve(handle_client, inet_addr, inet_port)

    return await start_server


def _build_server_func(iface, impl):
    iface_json = json.dumps(iface)

    async def handle_client(ws, path):
        await ws.send(iface_json)
        return await _handle_client(ws, impl)

    return handle_client


async def _handle_client(ws, impl):
    try:
        while True:
            cmd = await ws.recv()
            cmd = cmd.strip()
            cmd = json.loads(cmd)
            type_ = cmd['type']

            if type_ == 'invoke':
                await _handle_client_invoke(ws, cmd, impl)

            elif type_ == 'subscribe':
                await _handle_client_subscribe(ws, cmd)

            elif type_ == 'unsubscribe':
                await _handle_client_unsubscribe(ws, cmd)

    except websockets.exceptions.ConnectionClosed:
        print('...closed...')


async def _handle_client_invoke(ws, cmd, impl):
    id_ = cmd['id']
    path = cmd['path']
    args = cmd['args']
    func = impl[path]
    val = await func(*args)   # TODO: catch, serialize, and transmit any exception which is thrown by `func`.
    result = {
        'id': id_,
        'val': val,
    }
    result_json = json.dumps(result)
    await ws.send(result_json)


async def _handle_client_subscribe(ws, cmd):
    service = cmd['service']
    # TODO


async def _handle_client_unsubscribe(ws, cmd):
    service = cmd['service']
    # TODO


async def _demo():
    class Thing:
        async def export_foo(self, x):
            print('I am foo.')
            return x ** 3

    thing = Thing()

    server = await serve(thing)


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_demo())
    loop.run_forever()

