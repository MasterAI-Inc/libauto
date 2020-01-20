###############################################################################
#
# Copyright (c) 2017-2020 Master AI, Inc.
# ALL RIGHTS RESERVED
#
# Use of this library, in source or binary form, is prohibited without written
# approval from Master AI, Inc.
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
    iface = _serialize_interface(thing, name, set(whitelist_method_names))
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
        # For these generic objects, we'll only export
        # methods/functions which have 'export_' in the
        # name (for security reasons!).
        extra_export_names = (_get_extra_export_names(thing) | whitelist_method_names)
        exported = []
        for attr_name in dir(thing):
            if attr_name.startswith(EXPORT_PREFIX) or attr_name in extra_export_names:
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


def _serialize_method(f, name=None, send_wrapped_docs=True):
    # If `f` is a decorator, we want to dig in and find the inter-most "wrapped" function.
    #
    # **Note**: You may not always want to dig in and find the inter-most wrapped function,
    #           thus we've included the `send_wrapped_docs` parameter to this function.
    #           The only time you do *not* want to dig for the wrapped function is if the
    #           decorator changes the parameter list. For our use cases, this will not
    #           be the case thus we set `send_wrapped_docs` to True by default.
    f_outer = f
    f_inner = f
    while hasattr(f_inner, '__wrapped__') and send_wrapped_docs:
        f_inner = f_inner.__wrapped__

    if name is None:
        name = f_inner.__name__

    args = f_inner.__code__.co_varnames[:f_inner.__code__.co_argcount]   # consider instead: inspect.getfullargspec()
    is_method = False

    if hasattr(f_outer, '__self__'):
        # A bound method. Remove the first parameter from the signature
        # since it is included through python's crazy method binding
        # behavior. The other side of the RPC doesn't need to see this
        # first parameter.
        args = tuple(args[1:])
        is_method = True

    return {
        'name': name,
        'args': args,
        'defaults': f_inner.__defaults__,
        'module': f_inner.__module__,
        'doc': inspect.getdoc(f_inner) or inspect.getdoc(f_outer),   # <-- uses the super-method's __doc__ as needed
        'filename': f_inner.__code__.co_filename,
        'firstlineno': f_inner.__code__.co_firstlineno,
        'ismethod': is_method,
        'impl': f_outer,
        'is_async': inspect.iscoroutinefunction(f_outer),
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


def _get_extra_export_names(thing):
    m = getattr(thing, 'rpc_extra_exports', None)
    if m is None:
        return set()
    return set(m())

