import asyncio
import websockets

from auto.rpc.packer import pack, unpack
from auto.rpc.build_interface import build_interface


async def client(inet_addr='localhost', inet_port=7000):

    uri = f"ws://{inet_addr}:{inet_port}"

    ws = await websockets.connect(uri)

    iface_buf = await ws.recv()
    pubsub_channels_buf = await ws.recv()

    iface = unpack(iface_buf)
    pubsub_channels = unpack(pubsub_channels_buf)

    id_ = 0
    invoke_events = {}
    subscriptions = {}

    async def impl_transport(path, args):
        nonlocal id_
        id_here = id_
        id_ += 1
        event = asyncio.Event()
        invoke_events[id_here] = {
            'event': event,
        }
        cmd = {
            'type': 'invoke',
            'id': id_here,
            'path': path,
            'args': args,
        }
        cmd = pack(cmd)
        await ws.send(cmd)
        await event.wait()
        val = invoke_events[id_here]['val']
        del invoke_events[id_here]
        return val

    _, proxy_interface = build_interface(iface, impl_transport)

    async def read_ws():
        try:
            while True:
                message = await ws.recv()
                message = unpack(message)
                type_ = message['type']
                if type_ == 'invoke_result':
                    id_ = message['id']
                    val = message['val']
                    if id_ in invoke_events:
                        invoke_events[id_]['val'] = val
                        event = invoke_events[id_]['event']
                        event.set()
                elif type_ == 'publish':
                    channel = message['channel']
                    payload = message['payload']
                    callbacks = subscriptions.get(channel, [])
                    tasks = []
                    for c in callbacks:
                        task = asyncio.create_task(c(channel, payload))
                        tasks.append(task)
                    await asyncio.wait(tasks)

        except websockets.exceptions.ConnectionClosed:
            pass

    asyncio.create_task(read_ws())

    async def subscribe_func(channel, callback):
        if channel not in subscriptions:
            subscriptions[channel] = {callback}
            await ws.send(pack({
                'type': 'subscribe',
                'channel': channel,
            }))

        else:
            subscriptions[channel].add(callback)

        async def unsubscribe_func():
            subscriptions[channel].remove(callback)

            if len(subscriptions[channel]) == 0:
                del subscriptions[channel]
                await ws.send(pack({
                    'type': 'unsubscribe',
                    'channel': channel,
                }))

        return unsubscribe_func

    async def close():
        await ws.close()

    return proxy_interface, pubsub_channels, subscribe_func, close


async def _demo():
    proxy_interface, pubsub_channels, subscribe_func, close = await client()
    print(proxy_interface)
    print(pubsub_channels)

    async def callback(channel, payload):
        print('callback', channel, payload)

    await subscribe_func(pubsub_channels[0], callback)

    for i in range(4):
        result = await proxy_interface.foo(4 + i)
        print(result)

    await asyncio.sleep(15)

    await close()


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(_demo())
