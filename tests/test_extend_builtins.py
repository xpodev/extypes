import typing_extensions
import extypes

# `list` is actually the builtin type, but we import it so we get
# proper typing. Note that the static type checker doesn't recognize
# `[]` as an object of type list so it'll not add the extension methods.
from extypes import extend_type_with, extension, list, implement_protocol_on_type, Protocol


def test_extend_builtins():
    extypes.extend_builtin_types()

    assert hasattr(list, "map")

    assert [1, 2, 3].map((1).__add__) == [2, 3, 4]

    assert [1, 2, 3].reduce(int.__add__) == 6

def test_extend_builtins_with_magic():

    def _():
        ...

    function = type(_)

    implement_protocol_on_type(function, Protocol.Number)

    class CallableProtocol(typing_extensions.Protocol):
        def __call__(self, *args, **kwargs):
            ...

    class FunctionExtension(CallableProtocol):
        def __call__(self, *args, **kwargs):
            assert False, "This should never be called, it's just to make the type checker happy"

        @extension
        def __matmul__(self, other):

            def _(*args, **kwargs):
                return self(other(*args, **kwargs))
            return _

        @extension
        def __shl__(self, other):
            assert isinstance(other, (tuple, dict))

            def wrapper(*args, **kwargs):
                if isinstance(other, tuple):
                    return self(*other, *args, **kwargs)
                return self(*args, **other, **kwargs)
            return wrapper

    extend_type_with(function, FunctionExtension)

    def stringify(x):
        return str(x)

    def add(x, y):
        return x + y

    assert (stringify @ add)(1, 2) == "3"


def test_reverse_methods():
    class TupleExtensions(tuple):
        # since __add__ will override the default tuple.__add__ behavior, we need to save this
        tuple__add__ = tuple.__add__

        @extension
        def __add__(self, other):
            if isinstance(other, tuple):
                return TupleExtensions.tuple__add__(self, other)
            return NotImplemented

    class FunctionExtension:  # can't inherit from 'function'
        @extension
        def __radd__(self, other):
            assert isinstance(other, tuple)

            def wrapper(*args, **kwargs):
                return self(*other, *args, **kwargs)
            return wrapper

    def add(x, y):
        return x + y

    function = type(add)

    extend_type_with(function, FunctionExtension)
    extend_type_with(tuple, TupleExtensions)

    # tbh this doesn't yet work.
    # assert ((1, 2) + add) == 3
