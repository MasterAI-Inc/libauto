import asyncio
from auto.rpc.client import client


async def run():
    proxy_interface, pubsub_channels, subscribe_func, close = \
            await client('localhost', 7002)

    print(proxy_interface)

    caps = await proxy_interface.init()
    print(caps)

    version_iface = await proxy_interface.acquire('VersionInfo')
    print(version_iface)
    print(await version_iface.version())
    print(await version_iface.name())

    buzzer = await proxy_interface.acquire('Buzzer')
    await buzzer.play('!T240 L8 V7 agafaea dac+adaea fa<aa<bac#a dac#adaea f4')   # "Bach's fugue in D-minor"
    await buzzer.wait()

    await close()


if __name__ == '__main__':
    asyncio.run(run())

