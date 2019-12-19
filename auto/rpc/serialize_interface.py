###############################################################################
#
# Copyright (c) 2017-2018 AutoAuto, LLC
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from AutoAuto, LLC.
#
###############################################################################

"""
This module serializes Python objects into a human-readable interface
description. This interface description will be sent over the wire so that
the client may construct Python objects which look and feel like the original
objects.
"""

import inspect


EXPORT_PREFIX = 'export_'


def serialize_interface(thing, name='root', whitelist_method_names=()):
    """
    This is the main entry-point for serializing a Python object (`thing`).
    Not all methods/attributes of the object will be serialized; only those
    whose name starts with "export_" or which are listed in `whitelist_method_names`
    will be serialized. This is so that we are explicit about which operations
    become part of the RPC system, and we avoid accidental exposure of hidden/
    private/vulnerable methods.
    """
    iface = _serialize_interface(thing, name, whitelist_method_names)
    impl = _separate_implementation(iface)
    return iface, impl


def _serialize_interface(thing, name, whitelist_method_names):
    if inspect.isfunction(thing):
        return _serialize_function(thing, name)

    elif inspect.ismethod(thing):
        return _serialize_method(thing, name)

    elif inspect.isclass(thing):
        raise Exception('You may not serialize a class.')

    else:
        # We have some other type of object... maybe
        # a custom object, maybe a module, we don't know.
        # For these generic objects, we'll only expose
        # methods/functions which have 'export_' in the
        # name (for security reasons!).
        exported = []
        for attr_name in dir(thing):
            if attr_name.startswith(EXPORT_PREFIX) or attr_name in whitelist_method_names:
                if attr_name.startswith(EXPORT_PREFIX):
                    cropped_name = attr_name[len(EXPORT_PREFIX):]
                else:
                    cropped_name = attr_name
                attr = getattr(thing, attr_name)
                iface = _serialize_interface(attr, cropped_name, whitelist_method_names)
                exported.append(iface)
        return {
            'name': name,
            'typename': type(thing).__name__,
            'module': type(thing).__module__,
            'doc': inspect.getdoc(type(thing)),    # <-- uses the super-class's __doc__ as needed
            'ifaces': exported,
        }


def _serialize_function(f, name=None):
    # We can use the _serialize_method function, no worries.
    return _serialize_method(f, name)


def _serialize_method(f, name=None):
    if name is None:
        name = f.__name__

    args = f.__code__.co_varnames[:f.__code__.co_argcount]
    is_method = False

    if hasattr(f, '__self__'):
        # A bound method. Remove the first parameter from the signature
        # since it is included through python's crazy method binding
        # behavior. The other side of the RPC doesn't need to see this
        # first parameter.
        args = tuple(args[1:])
        is_method = True

    return {
        'name': name,
        'args': args,
        'defaults': f.__defaults__,
        'module': f.__module__,
        'doc': inspect.getdoc(f),   # <-- uses the super-method's __doc__ as needed
        'filename': f.__code__.co_filename,
        'firstlineno': f.__code__.co_firstlineno,
        'ismethod': is_method,
        'impl': f,
    }


def _separate_implementation(iface, prefix=''):
    if 'typename' in iface:
        # This is an object with inner stuff.
        name = iface['name']
        path = _build_path(prefix, name)
        iface['path'] = path
        impls = {}
        for iface in iface['ifaces']:
            impls.update(_separate_implementation(iface, path))
        return impls

    else:
        # This is just a single callable.
        name = iface['name']
        impl = iface.pop('impl')
        path = _build_path(prefix, name)
        iface['path'] = path
        return {path: impl}


def _build_path(prefix, name):
    if prefix == '':
        return name
    else:
        return prefix + '.' + name

