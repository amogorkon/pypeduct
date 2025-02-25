from __future__ import annotations

import pytest

from pypeduct.pyping import pyped


def test_basic_pipe():
    @pyped
    def basic_pipe() -> list[str]:
        result: list[str] = 5 >> str << list
        return result

    assert basic_pipe() == ["5"]


def test_complex_types():
    @pyped
    def complex_pipe() -> tuple[str, int, int]:
        a: list[int] = [1, 2, 3]
        b: dict[str, int] = {"a": 1}
        c: tuple[int, int, int] = (1, 2, 3)
        return a >> len >> str, b >> len, c >> len

    assert complex_pipe() == ("3", 1, 3)


def test_pipeline_inside_comprehension():
    @pyped
    def pipeline_function(x: int) -> list[str]:
        return [i >> (lambda x: x**2) >> str for i in range(5)]

    x = pipeline_function(5)

    assert x == ["0", "1", "4", "9", "16"]


def test_rshift_operator():
    @pyped
    def rshift_pipe() -> str:
        def wrap(text: str) -> str:
            return f"<{text}>"

        result: str = "content" >> wrap
        assert 3 >> 1 == 1
        return result

    assert rshift_pipe() == "<content>"


def test_nested_pyped():
    @pyped
    def nested_pyped() -> int:
        result: int = (5 >> (lambda x: x + 2)) >> (lambda x: x * 3)
        return result

    assert nested_pyped() == 21


def test_complex_expression_pipe():
    @pyped
    def complex_expression_pipe() -> int:
        expr: int = (2 + 3) * 4
        result: int = expr >> (lambda x: x - 5)
        return result

    assert complex_expression_pipe() == 15


def test_exception_handling_in_pipe():
    @pyped
    def exception_pipe() -> int:
        result: int = "test" >> int
        return result

    with pytest.raises(ValueError):
        exception_pipe()


def test_pipe_with_generator_expression():
    @pyped
    def generator_pipe() -> list[int]:
        def square(x: int) -> int:
            return x * x

        gen = (i for i in range(5))
        result: list[int] = list(gen) >> (lambda lst: [square(x) for x in lst])
        return result

    assert generator_pipe() == [0, 1, 4, 9, 16]


def test_variable_scope_in_exec():
    @pyped
    def context_test() -> str:
        var: str = "hello"
        result: str = var >> str.upper
        return result

    assert context_test() == "HELLO"


def test_pipe_with_lambda():
    @pyped
    def lambda_test() -> int:
        result: int = 5 >> (lambda x: x * x)
        return result

    assert lambda_test() == 25


def test_pipe_with_exception_in_function():
    @pyped
    def exception_in_function() -> int:
        def faulty_function(x: int) -> int:
            raise ValueError("Test exception")

        result: int = 5 >> faulty_function
        return result

    with pytest.raises(ValueError):
        exception_in_function()


def test_pipe_with_none():
    @pyped
    def none_pipe() -> bool:
        result: bool = None >> (lambda x: x is None)
        return result

    assert none_pipe()


def test_pipe_with_type_annotations():
    @pyped
    def type_annotation_test() -> int:
        result: int = 5 >> (lambda x: x * 2)
        return result

    assert type_annotation_test() == 10


def test_pipe_with_kwargs_in_function():
    @pyped
    def kwargs_function() -> str:
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        left_result: str = "Alyz" << greet(greeting="Hi")
        right_result: str = "Alyz" >> greet(greeting="Hi")
        assert left_result == right_result
        return right_result

    assert kwargs_function() == "Hi, Alyz!"


def test_pipe_with_multiple_pyped_in_one_expression():
    @pyped
    def multiple_pyped() -> int:
        result: int = 5 >> (lambda x: x + 1) >> (lambda x: x * 2) << (lambda x: x - 3)
        return result

    assert multiple_pyped() == 9


def test_pipe_with_unary_operator():
    @pyped
    def unary_operator_test() -> int:
        result: int = (-5) >> abs
        return result

    assert unary_operator_test() == 5


def test_pipe_with_chained_comparisons():
    @pyped
    def chained_comparison_test(x: int) -> bool:
        result: bool = (1 < x < 10) >> (lambda x: x)
        return result

    assert chained_comparison_test(5)
    assert not chained_comparison_test(0)


def test_syntax_error_in_pyped():
    faulty_code = """
@pyped
def syntax_error_func():
    result = 5 > >
    return result
"""
    with pytest.raises(SyntaxError) as context:
        exec(faulty_code, globals())

    assert "invalid syntax" in str(context.value)


def test_pipe_with_class_method_inside():
    class MyClass:
        def __init__(self, value: int) -> None:
            self.value = value

        @pyped
        def multiply(self, x: int) -> int:
            return x >> (lambda y: y * self.value)

    instance = MyClass(3)

    result = instance.multiply(5)
    assert result == 15


def test_pipe_with_method_inside():
    class MyClass:
        def __init__(self, value: int) -> None:
            self.value = value

        @pyped
        def multiply(self, x: int) -> int:
            return x >> (lambda y: y * self.value)

    instance = MyClass(3)

    result = instance.multiply(5)
    assert result == 15


def test_pipe_with_method_outside():
    @pyped
    class MyClass:
        def __init__(self, value: int) -> None:
            self.value = value

        def multiply(self, x: int) -> int:
            return self.value >> (lambda y: y * x)

    instance = MyClass(3)
    result = instance.multiply(5)
    assert result == 15


def test_pipe_in_classmethod():
    class MyClass:
        @classmethod
        @pyped
        def class_method(cls, x: int) -> str:
            return x >> str

    result = MyClass.class_method(42)
    assert result == "42"


def test_pipe_in_staticmethod():
    class MyClass:
        @staticmethod
        @pyped
        def static_method(x: int) -> str:
            return x >> str

    result = MyClass.static_method(42)
    assert result == "42"


def test_pipe_with_partial_function():
    from functools import partial

    @pyped
    def partial_func_pipe() -> int:
        def multiply(a: int, b: int) -> int:
            return a * b

        multiply_by_two = partial(multiply, b=2)
        result: int = 5 >> multiply_by_two
        return result

    assert partial_func_pipe() == 10


def test_class_with_slots():
    class Test:
        __slots__ = ("id",)

        def __init__(self, id: int) -> None:
            self.id = id

        @pyped
        def foo(self) -> int:
            return self.id >> str >> list >> len

    t = Test(123)
    assert t.foo() == 3


def test_pipe_with_custom_object():
    class CustomObject:
        def __init__(self, value: int) -> None:
            self.value = value

        def foo(self, x: CustomObject) -> int:
            return x.value + self.value

    @pyped
    def custom_object_pipe() -> int:
        obj = CustomObject(10)
        return obj >> obj.foo

    assert custom_object_pipe() == 20


def test_side_effects_order():
    side_effects = []

    def func_a(x: int) -> int:
        side_effects.append("A")
        return x + 1

    def func_b(x: int, y: int) -> int:
        side_effects.append("B")
        return x * y

    @pyped
    def pipeline_with_side_effects() -> int:
        return (a := 3) >> func_a >> func_b(a)

    result = pipeline_with_side_effects()
    assert result == 12  # (3 + 1) * 3
    assert side_effects == ["A", "B"]


@pyped
def test_pipeline_in_nested_functions() -> int:
    def outer_function() -> int:
        def inner_function() -> int:
            return (x := 5) >> (lambda y: y * y)

        return inner_function()

    assert outer_function() == 25


def test_pipeline_inside_conditional():
    @pyped
    def pipeline_in_conditional(flag: bool) -> str:
        if flag:
            (msg := "Hello") >> (lambda x: x + " World") >> print
        else:
            (msg := "Goodbye") >> (lambda x: x + " World") >> print
        return msg

    assert pipeline_in_conditional(True) == "Hello"
    assert pipeline_in_conditional(False) == "Goodbye"


def test_conditional_pipeline_side_effects():
    side_effects = []

    def effect(x: int) -> int:
        side_effects.append(f"Effect {x}")
        return x * x

    @pyped
    def conditional_pipeline(flag: bool) -> int:
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


def test_pipeline_inside_loop():
    @pyped
    def pipeline_in_loop() -> list[int]:
        results = []
        for i in range(3):
            (val := i) >> (lambda x: x * 2) >> results.append
        assert val == 2
        return results

    assert pipeline_in_loop() == [0, 2, 4]


def test_pipe_with_walrus_tower():
    @pyped
    def foo() -> tuple[float, int]:
        def bar(x: int) -> int:
            return x + 1

        x = (
            5
            >> (lambda x: x * 2)
            >> (y := bar)
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )
        return x, y

    assert foo() == (60.0, 11)


def test_pipe_with_walrus_lambda_tower():
    @pyped
    def foo() -> tuple[float, int]:
        x = (
            5
            >> (lambda x: x * 2)
            >> (y := (lambda x: x + 1))
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )
        return x, y

    assert foo() == (60.0, 11)


def test_chained_walrus_assignments():
    @pyped
    def chained_walrus() -> tuple[int, int, int]:
        (a := 1) >> (b := lambda x: x + 1) >> (c := lambda x: x * 2)
        return a, b, c

    assert chained_walrus() == (1, 2, 4)


def test_multiple_walrus_in_single_statement():
    @pyped
    def multiple_walrus() -> tuple[int, int, tuple[int, int, int, int]]:
        z = ((a := 2), (b := 3)) >> (lambda x: x * 2)
        return a, b, z

    assert multiple_walrus() == (2, 3, (2, 3, 2, 3))


def test_pipeline_in_generator_expression():
    @pyped
    def pipeline_in_generator() -> tuple[list[int], int]:
        gen = ((x := i) >> (lambda y: y * 2) for i in range(3))
        return list(gen), x

    result, last_x = pipeline_in_generator()
    assert result == [0, 2, 4]
    assert last_x == 2


def test_pipe_with_decorated_function():
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs) + 3

        return wrapper

    @decorator
    @pyped
    def decorated_func() -> int:
        result: int = 5 >> (lambda x: x * 2)
        return result

    assert decorated_func() == 13  # (5 * 2) + 3


def test_invalid_operator_transformation():
    @pyped
    def invalid_operator() -> int:
        result: int = 5 + (lambda x: x * 2)
        return result

    with pytest.raises(TypeError):
        invalid_operator()


def test_interleaved_side_effects():
    side_effects = []

    def func_x(x: int) -> int:
        side_effects.append("X")
        return x + 1

    def func_y(y: int) -> int:
        side_effects.append("Y")
        return y * 2

    @pyped
    def complex_pipeline() -> tuple[int, int]:
        ((a := 1) >> func_x, (b := 2) >> func_y) >> (lambda x: x[0] + x[1])
        return a, b

    result = complex_pipeline()
    assert result == (1, 2)
    assert side_effects == ["X", "Y"]


def test_multiple_assignments_with_dependencies():
    @pyped
    def multiple_assignments() -> tuple[int, int]:
        (((a := 2) >> (lambda x: x + 3)), (b := a * 2)) >> (lambda x: x[0] + b)
        return a, b

    assert multiple_assignments() == (2, 4)


def test_mutable_object_side_effects():
    class Counter:
        def __init__(self) -> None:
            self.count = 0

        def increment(self, _: int) -> Counter:
            self.count += 1
            return self

        def multiply(self, factor: int) -> Counter:
            self.count *= factor
            return self

    @pyped
    def pipeline_with_mutable_object() -> int:
        counter = Counter()
        counter >> counter.increment >> counter.increment >> (lambda c: c.multiply(5))
        return counter.count

    assert pipeline_with_mutable_object() == 10  # ((0 + 1 + 1) * 5)


def test_method_pipe_in_property():
    class MyClass:
        def __init__(self, value: int) -> None:
            self._value = value

        @property
        @pyped
        def value(self) -> str:
            return self._value >> str

    instance = MyClass(100)
    assert instance.value == "100"
