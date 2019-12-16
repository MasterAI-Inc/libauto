import inspect
import cio


def build_cio_map():
    m = {}

    abs_classes = inspect.getmembers(cio, predicate=inspect.isabstract)

    for class_name, class_type in abs_classes:
        methods = inspect.getmembers(class_type, predicate=inspect.isfunction)
        m[class_name] = [method_name for method_name, method_ref in methods]

    return m


def get_abc_superclass_name(obj):
    mro = inspect.getmro(type(obj))
    superclass = mro[1]
    assert inspect.isabstract(superclass)
    superclass_name = superclass.__name__
    return superclass_name

