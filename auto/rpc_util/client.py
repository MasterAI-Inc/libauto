import asyncio
import websockets
import json

from auto.rpc_util.build_interface import build_interface


async def client(inet_addr='localhost', inet_port=7000):

    uri = f"ws://{inet_addr}:{inet_port}"

    ws = await websockets.connect(uri)

    iface_json = await ws.recv()

    iface = json.loads(iface_json)

    async def impl_transport(path, args):
        cmd = json.dumps([path, args])
        await ws.send(cmd)
        result_json = await ws.recv()
        result = json.loads(result_json)
        return result

    _, proxy_interface = build_interface(iface, impl_transport)

    async def close():
        await ws.close()

    return proxy_interface, close


async def _demo():
    proxy_interface, close = await client()
    print(proxy_interface)

    result = await proxy_interface.foo(4)
    print(result)

    await close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_demo())

