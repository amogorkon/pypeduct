from __future__ import annotations

import ast
import sys

import pytest

from pypeduct.pyping import pyped
from pypeduct.transformer import PipeTransformError


def test_transformer_error_propagation():
    original_visit_BinOp = ast.NodeTransformer.visit_BinOp

    def faulty_visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        raise PipeTransformError("Simulated AST error")

    try:
        ast.NodeTransformer.visit_BinOp = faulty_visit_BinOp
        with pytest.raises(PipeTransformError) as context:

            @pyped
            def faulty_transform() -> str:
                result = 5 >> str
                return result

        assert "AST transformation failed" in str(context.value)
    finally:
        ast.NodeTransformer.visit_BinOp = original_visit_BinOp


def test_compilation_failure_handling():
    original_compile = compile

    def faulty_compile(*args, **kwargs) -> None:
        raise SyntaxError("Simulated compilation error")

    try:
        sys.modules["builtins"].compile = faulty_compile
        with pytest.raises(SyntaxError("Simulated compilation error")) as context:

            @pyped
            def faulty_compilation() -> str:
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


def test_pipe_with_partial_methods():
    from functools import partial

    class MyClass:
        def __init__(self, value: int) -> None:
            self._value = value

        @pyped
        def value(self) -> int:
            return self._value >> (lambda x: x * 2)

        def multiply(self, factor: int) -> int:
            return self.value() * factor

    def foo() -> None:
        instance = MyClass(5)
        result1 = partial(instance.multiply)(2)
        assert result1 == 10

    foo()


def test_pipe_with_custom_object_walrus():
    class CustomObject:
        def __init__(self, value: int) -> None:
            self.value = value

        def increment(self, _: None) -> CustomObject:
            self.value += 1
            return self

        def foo(self, x: "CustomObject") -> int:
            return x.value * 2

    @pyped
    def custom_object_pipe() -> int:
        return (obj := CustomObject(10)) >> obj.increment >> obj.increment >> obj.foo

    assert custom_object_pipe() == 24


def test_tuple_unpacking_lambda():
    @pyped
    def multiple_assignments() -> tuple[int, int]:
        return (1, 2) >> (lambda x, y: x + y)

    assert multiple_assignments() == 3


def test_class_pipe_in_property():
    @pyped
    class MyClass:
        def __init__(self, value: int) -> None:
            self._value = value

        @property
        def value(self) -> str:
            return self._value >> str

    instance = MyClass(100)
    assert instance.value == "100"
