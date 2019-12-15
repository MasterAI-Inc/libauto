import inspect


EXPORT_PREFIX = 'export_'


def serialize_interface(thing, name='root', whitelist_method_names=()):
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
            'doc': type(thing).__doc__,
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
        'doc': f.__doc__,
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

