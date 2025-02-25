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


def test_pipe_with_walrus():
    @pyped
    def foo():
        x = (
            5
            >> (lambda x: x * 2)
            >> (y := lambda x: x + 1)
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )
        return x, y

    assert foo() == (60.0, 6)


def test_pipeline_inside_loop():
    @pyped
    def pipeline_in_loop():
        results = []
        for i in range(3):
            (val := i) >> (lambda x: x * 2) >> results.append
        assert val == 2
        return results

    assert pipeline_in_loop() == [0, 2, 4]


def test_pipeline_inside_conditional():
    @pyped
    def pipeline_in_conditional(flag):
        if flag:
            (msg := "Hello") >> (lambda x: x + " World") >> print
        else:
            (msg := "Goodbye") >> (lambda x: x + " World") >> print
        return msg

    assert pipeline_in_conditional(True) == "Hello"
    assert pipeline_in_conditional(False) == "Goodbye"


def test_multiple_walrus_in_single_statement():
    @pyped
    def multiple_walrus():
        ((a := 2), (b := 3)) >> (lambda x, y: x + y)
        return a, b

    assert multiple_walrus() == (2, 3)


def test_mutable_object_side_effects():
    class Counter:
        def __init__(self):
            self.count = 0

        def increment(self):
            self.count += 1
            return self

        def multiply(self, factor):
            self.count *= factor
            return self

    @pyped
    def pipeline_with_mutable_object():
        counter = Counter()
        counter >> counter.increment >> counter.increment >> (lambda c: c.multiply(5))
        return counter.count

    assert pipeline_with_mutable_object() == 10  # ((0 + 1 + 1) * 5)


def test_pipe_with_walrus():
    @pyped
    def foo():
        x = (
            5
            >> (lambda x: x * 2)
            >> (lambda x: (y := x + 1))
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )
        return x, y

    assert foo() == (60.0, 11)


def test_chained_walrus_assignments():
    @pyped
    def chained_walrus():
        (a := 1) >> (b := lambda x: x + 1) >> (c := lambda x: x * 2)
        return a, b, c

    assert chained_walrus() == (1, 2, 4)


def test_conditional_pipeline_side_effects():
    side_effects = []

    def effect(x):
        side_effects.append(f"Effect {x}")
        return x * x

    @pyped
    def conditional_pipeline(flag):
        if flag:
            (res := 2) >> effect >> print
        else:
            (res := 3) >> effect >> print
        return res

    assert conditional_pipeline(True) == 2
    assert side_effects == ["Effect 2"]
    side_effects.clear()
    assert conditional_pipeline(False) == 3
    assert side_effects == ["Effect 3"]


def test_pipeline_in_generator_expression():
    @pyped
    def pipeline_in_generator():
        gen = ((x := i) >> (lambda y: y * 2) for i in range(3))
        return list(gen), x

    result, last_x = pipeline_in_generator()
    assert result == [0, 2, 4]
    assert last_x == 2  # Last value assigned to x


def test_multiple_assignments_with_dependencies():
    @pyped
    def multiple_assignments():
        (((a := 2) >> (lambda x: x + 3)), (b := a * 2)) >> (lambda x, y: x + y)
        return a, b

    assert multiple_assignments() == (2, 4)


def test_interleaved_side_effects():
    side_effects = []

    def func_x(x):
        side_effects.append("X")
        return x + 1

    def func_y(y):
        side_effects.append("Y")
        return y * 2

    @pyped
    def complex_pipeline():
        ((a := 1) >> func_x, (b := 2) >> func_y) >> (lambda x, y: x + y)
        return a, b

    result = complex_pipeline()
    assert result == (1, 2)
    assert side_effects == ["X", "Y"]
