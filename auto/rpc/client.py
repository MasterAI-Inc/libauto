import asyncio
import websockets
import json

from auto.rpc.build_interface import build_interface


async def client(inet_addr='localhost', inet_port=7000):

    uri = f"ws://{inet_addr}:{inet_port}"

    ws = await websockets.connect(uri)

    iface_json = await ws.recv()

    iface = json.loads(iface_json)

    id_ = 0

    async def impl_transport(path, args):
        nonlocal id_
        id_here = id_
        id_ += 1
        cmd = {
            'type': 'invoke',
            'id': id_here,
            'path': path,
            'args': args,
        }
        cmd = json.dumps(cmd)
        await ws.send(cmd)
        result_json = await ws.recv()
        result = json.loads(result_json)
        assert result['id'] == id_here    # <-- Assumes no other parallel coroutine is using this same transport. We _could_ allow such a thing if we were more clever, but for now we'll just assert that we only have one coroutine using this transport.
        return result['val']

    _, proxy_interface = build_interface(iface, impl_transport)

    async def close():
        await ws.close()

    return proxy_interface, close


async def _demo():
    proxy_interface, close = await client()
    print(proxy_interface)

    for i in range(4):
        result = await proxy_interface.foo(4)
        print(result)

    await close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_demo())

