import types
from pprint import pprint

from serialize_interface import serialize_interface
from build_interface import build_interface


class OtherClass:
    """This is my other class."""
    def __init__(self):
        self.whatever = 99

    def not_exported(self, x):
        return x * x

    def export_thing(self, a, b=4, c=6):
        """This is the method named `thing`."""
        return a * b * c


class MyClass:
    """This is my class!"""
    def __init__(self):
        self.abc = 4
        self.export_abcd = lambda theparam: theparam**2
        self.export_field = OtherClass()

    def method(self, x, y, z=3):
        print('hi')

    def export_foobar(self, x, y, z=3):
        """This is foobar!!!"""
        print('hi', self.abc)


thing = MyClass()

iface, impl = serialize_interface(thing)
pprint(iface)
pprint(impl)


def impl_transport(path, args):
    print(args)
    return impl[path](*args)

_, rpc_client = build_interface(iface, impl_transport)


print(rpc_client)
print(rpc_client.__doc__)

print(rpc_client.field)
print(rpc_client.field.__doc__)

print('abcd', rpc_client.abcd(5))
print()

print('foobar', rpc_client.foobar(1, 2))
print()

print('thing', rpc_client.field.thing(101))
print()

