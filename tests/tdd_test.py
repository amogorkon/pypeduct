import ast
import sys

import pytest

from pypeduct.pyping import pyped
from pypeduct.transformer import PipeTransformError


def test_pipe_with_class_method():
    class MyClass:
        def __init__(self, value):
            self.value = value

        @pyped
        def multiply(self, x: int) -> int:
            return x * self.value

    instance = MyClass(3)
    result = 5 >> instance.multiply
    assert result == 15


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


def test_syntax_error_in_pyped():
    faulty_code = """
@pyped
def syntax_error_func():
    result = 5 >>
    return result
"""
    with pytest.raises(PipeTransformError) as context:
        exec(faulty_code, globals())
    assert "Syntax error" in str(context.value)


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


def test_pipe_with_partial_function():
    from functools import partial

    @pyped
    def partial_func_pipe():
        def multiply(a, b):
            return a * b

        multiply_by_two = partial(multiply, b=2)
        result = 5 >> multiply_by_two
        return result

    assert partial_func_pipe() == 10


def test_custom_exception_message():
    faulty_code = """
@pyped
def invalid_syntax():
    return eval('invalid code')
"""
    with pytest.raises(PipeTransformError) as context:
        exec(faulty_code, globals())
    assert "Could not retrieve source code" in str(context.value)


def test_pipe_with_async_function_in_sync_context():
    @pyped
    def async_in_sync():
        async def async_double(x):
            return x * 2

        # Attempting to await in a sync function will raise an error
        result = 5 >> async_double
        return result

    with pytest.raises(TypeError):
        async_in_sync()


def test_pipe_with_custom_object():
    class CustomObject:
        def __init__(self, value):
            self.value = value

        def increment(self):
            self.value += 1
            return self

    @pyped
    def custom_object_pipe():
        obj = CustomObject(10)
        obj = obj >> CustomObject.increment >> CustomObject.increment
        return obj.value

    assert custom_object_pipe() == 12


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
