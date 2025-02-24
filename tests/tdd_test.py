import ast
import sys

import pytest

from pypeduct.pyping import pyped
from pypeduct.transformer import PipeTransformError


def test_transformer_error_propagation():
    original_visit_BinOp = ast.NodeTransformer.visit_BinOp

    def faulty_visit_BinOp(self, node):
        raise PipeTransformError("Simulated AST error")

    try:
        ast.NodeTransformer.visit_BinOp = faulty_visit_BinOp
        with pytest.raises(PipeTransformError) as context:

            @pyped
            def faulty_transform():
                result = 5 >> str
                return result

        assert "AST transformation failed" in str(context.value)
    finally:
        ast.NodeTransformer.visit_BinOp = original_visit_BinOp


def test_invalid_operator_transformation():
    @pyped
    def invalid_operator():
        result = 5 + (lambda x: x * 2)
        return result

    assert isinstance(invalid_operator(), type((lambda x: x * 2)))


def test_pipe_in_property():
    class MyClass:
        def __init__(self, value):
            self._value = value

        @property
        @pyped
        def value(self) -> str:
            return self._value >> str

    instance = MyClass(100)
    assert instance.value == "100"


def test_compilation_failure_handling():
    original_compile = compile

    def faulty_compile(*args, **kwargs):
        raise SyntaxError("Simulated compilation error")

    try:
        sys.modules["builtins"].compile = faulty_compile
        with pytest.raises(SyntaxError("Simulated compilation error")) as context:

            @pyped
            def faulty_compilation():
                result = 5 >> str
                return result

        assert "Compilation failed" in str(context.value)
    finally:
        sys.modules["builtins"].compile = original_compile


def test_custom_exception_message():
    faulty_code = """
@pyped
def invalid_syntax():
    return eval('invalid code')
"""
    with pytest.raises(PipeTransformError) as context:
        exec(faulty_code, globals())
    assert "Could not retrieve source code" in str(context.value)


def test_pipe_with_decorated_function():
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs) + 1

        return wrapper

    @pyped
    @decorator
    def decorated_func():
        result = 5 >> (lambda x: x * 2)
        return result

    assert decorated_func() == 11  # (5 * 2) + 1


def test_pipe_with_property_decorator():
    class MyClass:
        def __init__(self, value):
            self._value = value

        @property
        @pyped
        def value(self) -> int:
            return self._value >> (lambda x: x * 2)

    instance = MyClass(10)
    assert instance.value == 20


def test_pipe_with_partial_methods():
    from functools import partial

    class MyClass:
        def __init__(self, value):
            self._value = value

        def value(self) -> int:
            return self._value >> (lambda x: x * 2)

    result = 5 >> partial(instance.multiply)
    assert result == 10

    result = partial(instance.multiply) << 5


def test_pipe_with_custom_object_walrus():
    class CustomObject:
        def __init__(self, value):
            self.value = value

        def increment(self, _):
            self.value += 1
            return self

        def foo(self, x):
            return x.value * 2

    @pyped
    def custom_object_pipe():
        (obj := CustomObject(10)) >> obj.increment >> obj.increment >> obj.foo
        return obj

    assert custom_object_pipe() == 24
    return custom_object_pipe()
