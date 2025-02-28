"""Test-driven development tests, expected to fail."""

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


def test_tuple_unpacking_lambda():
    @pyped
    def multiple_assignments() -> tuple[int, int]:
        return (1, 2) >> (lambda x, y: x + y)

    assert multiple_assignments() == 3


def test_nested_pipelines():
    @pyped
    def nested_pipeline(x: int) -> int:
        return x >> (lambda val: val + 1 >> (lambda v: v * 2))

    assert nested_pipeline(5) == 12  # 5 + 1 = 6, 6 * 2 = 12


def test_exception_group_handling_pipe():
    def error_func_1(x):
        raise ValueError("Error 1")

    def error_func_2(x):
        raise TypeError("Error 2")

    @pyped
    def exception_group_pipeline(x):
        try:
            return x >> error_func_1 >> error_func_2
        except ExceptionGroup as eg:
            return ", ".join(str(e) for e in eg.exceptions)

    assert exception_group_pipeline(5) == "Error 1, Error 2"


def test_pipe_transform_error_context():
    def error_func(x):
        raise ValueError("Contextual Error")

    @pyped
    def context_error_pipeline(x):
        try:
            return x >> error_func
        except PipeTransformError as e:
            assert "context_error_pipeline" in e.context
            return "Caught PipeTransformError with context"
        except Exception:
            return "Caught other exception"

    assert context_error_pipeline(5) == "Caught PipeTransformError with context"
