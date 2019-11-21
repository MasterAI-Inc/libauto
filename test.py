import types
from pprint import pprint

from serialize_interface import serialize_interface
from build_interface import build_interface


class OtherClass:
    def __init__(self):
        self.whatever = 99

    def not_exported(self, x):
        return x * x

    def export_thing(self, a, b=4, c=6):
        return a * b * c


class MyClass:
    def __init__(self):
        self.abc = 4
        self.export_abcd = lambda x: x*x
        self.export_field = OtherClass()

    def method(self, x, y, z=3):
        print('hi')

    def export_foobar(self, x, y, z=3):
        print('hi')


thing = MyClass()

iface, impl = serialize_interface(thing)
pprint(iface)
pprint(impl)

def impl_transport(path, args):
    return impl[path](*args)

_, rpc_client = build_interface(iface, impl_transport)

print(_)

print(rpc_client)

print('abcd', rpc_client.abcd(5))
print()

print('foobar', rpc_client.foobar(1, 2))
print()

print('thing', rpc_client.field.thing(101))
print()

