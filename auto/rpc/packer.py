USE_JSON = False


if USE_JSON:

    import json

    def pack(obj):
        buf = json.dumps(obj)
        return buf

    def unpack(buf):
        obj = json.loads(buf)
        return obj


else:

    import msgpack

    def pack(obj):
        buf = msgpack.packb(obj, use_bin_type=True)
        return buf

    def unpack(buf):
        obj = msgpack.unpackb(buf, use_list=False, raw=False)
        return obj

