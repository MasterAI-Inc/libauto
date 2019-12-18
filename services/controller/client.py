import asyncio
from auto.rpc.client import client


_PROXY_INTERFACE = None


async def init():
    global _PROXY_INTERFACE, _CAPS

    if _PROXY_INTERFACE is None:
        _PROXY_INTERFACE, pubsub_channels, subscribe_func, close = \
                await client('localhost', 7002)
        _CAPS = await _PROXY_INTERFACE.init()

    return _CAPS


async def acquire(capability_id):
    if _PROXY_INTERFACE is None:
        raise Exception("You must first call `init()` from this module.")

    capability_obj = await _PROXY_INTERFACE.acquire(capability_id)
    return capability_obj


async def release(capability_obj):
    if _PROXY_INTERFACE is None:
        raise Exception("You must first call `init()` from this module.")

    rpc_guid = await capability_obj.get_rpc_guid()
    await _PROXY_INTERFACE.release(rpc_guid)


async def _run():
    caps = await init()
    print(caps)

    version_iface = await acquire('VersionInfo')
    print(version_iface)
    print(await version_iface.version())
    print(await version_iface.name())

    buzzer_iface = await acquire('Buzzer')
    print(buzzer_iface)
    await buzzer_iface.play('!T240 L8 V7 agafaea dac+adaea fa<aa<bac#a dac#adaea f4')   # "Bach's fugue in D-minor"
    await buzzer_iface.wait()

    await release(buzzer_iface)
    await release(version_iface)


if __name__ == '__main__':
    asyncio.run(_run())

