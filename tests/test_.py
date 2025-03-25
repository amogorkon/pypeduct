"""Core tests to quickly check the basic functionality of the library on every edit."""

from __future__ import annotations

import math
from functools import partial

import pytest

from pypeduct import pyped


def test_no_pipes():
    @pyped
    def no_pipeline(x):
        return x + 1

    assert no_pipeline(5) == 6  # 5 + 1 = 6


def test_no_pipeline_but_pyped_called():
    @pyped()
    def no_pipeline_but_pyped(x):
        return x

    assert no_pipeline_but_pyped(5) == 5


def test_external_function():
    @pyped
    def compute_square_root():
        return 16 >> math.sqrt  # math.sqrt defined outside our module

    assert compute_square_root() == 4.0


def test_builtin_function():
    @pyped
    def compute_length():
        return [1, 2, 3] >> len  # len is a built-in function

    assert compute_length()


def test_walrus_hof():  # sourcery skip: simplify-empty-collection-comparison
    @pyped
    def test():
        X = [1, 2, 3] >> (ret := map(str)) >> " ".join
        # if you think list(ret) == ["1", "2", "3"] WRONG! ret is consumed by join, so ret is empty => []
        assert list(ret) == []
        return X

    assert test() == "1 2 3"


def test_pipe_with_complex_default_expression():
    complex_default = [x * 2 for x in range(3)]

    @pyped
    def complex_default_expr_pipeline(x=complex_default):
        return x >> (lambda val: val)

    assert complex_default_expr_pipeline() == [0, 2, 4]


def test_simple_diff():
    def diff(a, b):
        return a - b

    @pyped
    def compute_length():
        return 3 >> diff(1)  # the simplest order-dependent function with two args

    assert compute_length() == 2


def test_pipe_with_recursive_function():
    @pyped
    def recursive_pipeline(n):
        if n <= 0:
            return 0 >> (lambda x: x)
        else:
            return n >> (lambda x: x + recursive_pipeline(n - 1))

    assert recursive_pipeline(5) == 15


def test_function_with_multiple_default_args():
    @pyped
    def compute():
        def add_numbers(x, y=10, z=5):
            return x + y + z

        return 5 >> add_numbers

    assert compute() == 20


def test_function_with_keyword_only_args():
    @pyped
    def process_data():
        def transform(data, *, scale=1):
            return [x * scale for x in data]

        return [1, 2, 3] >> transform

    assert process_data() == [1, 2, 3]


def test_basic_pipe():
    @pyped
    def basic_pipe() -> list[str]:
        result: list[str] = 5 >> str >> list
        return result

    assert basic_pipe() == ["5"]


def test_pipe_with_strings():
    def add_parts(start="hello ", middle="world", end="!"):
        return start + middle + end

    @pyped
    def test():
        return ("cruel", "world") >> " ".join >> add_parts(middle=...)

    assert test() == "hello cruel world!"


def test_pipe_with_user_defined_function_reference():
    def increment_func(x):
        return x + 1

    @pyped
    def user_func_ref_pipeline(x):
        return x >> increment_func >> increment_func

    assert user_func_ref_pipeline(5) == 7


def test_tertiary_operator():
    @pyped
    def ternary_operator(x: int) -> int:
        return x >> ((lambda y: y + 1) if x % 2 == 0 else (lambda y: y - 1))

    assert ternary_operator(1) == 0  # (1 - 1) => 0
    assert ternary_operator(2) == 3  # (2 + 1) => 3


def test_binary_shift_vs_pipe():
    @pyped
    def binary_shift_right_with_pipe(x: int) -> int:
        return x >> 2

    def binary_shift_right_without_pipe(x: int) -> int:
        return x >> 2

    @pyped
    def binary_shift_left_with_pipe(x: int) -> int:
        return x << 2

    def binary_shift_left_without_pipe(x: int) -> int:
        return x << 2

    with pytest.raises(TypeError):
        binary_shift_right_with_pipe(5)

    assert binary_shift_right_without_pipe(5) == 5 >> 2
    assert binary_shift_left_with_pipe(5) == 5 << 2 == binary_shift_left_without_pipe(5)


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


def test_placeholder_position():
    def addd(a, b, c):
        return a + b + c

    @pyped
    def pipeline():
        return 2 >> addd(1, ..., 3)

    assert pipeline() == 6


def test_rshift_operator():
    @pyped
    def rshift_pipe() -> str:
        def wrap(text: str) -> str:
            return f"<{text}>"

        result: str = "content" >> wrap
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

        right_result: str = "Alyz" >> greet(greeting="Hi")
        return right_result

    assert kwargs_function() == "Hi, Alyz!"


def test_pipe_with_multiple_pyped_in_one_expression():
    @pyped
    def multiple_pyped() -> int:
        result: int = 5 >> (lambda x: x + 1) >> (lambda x: x * 2) >> (lambda x: x - 3)
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


def test_pipeline_inside_conditional():
    @pyped
    def pipeline_in_conditional(flag: bool) -> str:
        if flag:
            (msg := "Hello") >> (lambda x: f"{x} World") >> print
        else:
            (msg := "Goodbye") >> (lambda x: f"{x} World") >> print
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


def test_pipe_with_walrus_tower_kwargs():
    @pyped
    def foo() -> tuple[float, int]:
        def bar(x: int, /, *, baz: int) -> int:
            return x + baz

        x = (
            5
            >> (lambda x: x * 2)
            >> (y := bar(baz=1))
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )
        return x, y

    assert foo() == (60.0, 11)


def test_pipe_with_walrus_tower():
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


def test_pipeline_in_nested_functions() -> int:
    @pyped
    def outer_function() -> int:
        def inner_function() -> int:
            return (x := 5) >> (lambda y: y * y)

        return inner_function()

    assert outer_function() == 25


@pyped
def test_pipeline_in_nested_functions2() -> int:
    def outer_function() -> int:
        def inner_function() -> int:
            return (x := 5) >> (lambda y: y * y)

        return inner_function()

    assert outer_function() == 25


def test_class_with_other_decorators():
    def validate(cls):
        cls.validated = True
        return cls

    @pyped
    @validate
    class DataProcessor:
        def process(self, x: int) -> int:
            return x >> (lambda y: y + 1)

    # Check if @validate decorator was preserved
    assert hasattr(DataProcessor, "validated"), "Class lost other decorators!"
    # Check pipeline transformation
    assert DataProcessor().process(3) == 4


def test_class_level_variables():
    @pyped
    class Multiplier:
        factor: int = 2

        def apply(self, x: int) -> int:
            return x >> (lambda y: y * self.factor)

    instance = Multiplier()
    assert instance.apply(5) == 10, "Class-level variable not resolved!"


def test_decorator_stripping():
    def decorator(cls):
        cls.marked = True
        return cls

    @pyped
    @decorator
    class TestClass:
        pass

    assert hasattr(TestClass, "marked"), "All decorators were stripped!"


def test_instance_variable_interaction():
    @pyped
    class Stateful:
        def __init__(self, base: int):
            self.base = base

        def calculate(self) -> int:
            return self.base >> (lambda x: x**2)

    instance = Stateful(4)
    assert instance.calculate() == 16, "Instance variable access failed!"


def test_pipe_with_closure_reference():
    def create_incrementor_closure(inc):
        def incrementor(x):
            return x + inc

        return incrementor

    increment_by_1 = create_incrementor_closure(1)

    @pyped
    def closure_ref_pipeline(x):
        return x >> increment_by_1 >> increment_by_1

    assert closure_ref_pipeline(5) == 7


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


def test_pipeline_inside_conditional():
    @pyped
    def pipeline_inside_conditional(flag: bool) -> str:
        if flag:
            msg = "Hello" >> (lambda x: x + " World")
        else:
            msg = "Goodbye" >> (lambda x: x + " World")
        return msg

    assert pipeline_inside_conditional(True) == "Hello World"
    assert pipeline_inside_conditional(False) == "Goodbye World"


def test_pipeline_inside_conditional_walrus():
    @pyped
    def pipeline_in_conditional(flag: bool) -> str:
        if flag:
            (msg := "Hello") >> (lambda x: x + " World")
        else:
            (msg := "Goodbye") >> (lambda x: x + " World")
        return msg

    assert pipeline_in_conditional(True) == "Hello"  # Expect "Hello"
    assert pipeline_in_conditional(False) == "Goodbye"


def test_conditional_expression_pipeline():
    @pyped
    def conditional_pipeline(flag: bool) -> str:
        msg = "Hello" if flag else "Goodbye" >> (lambda x: x + " World")
        return msg

    assert conditional_pipeline(True) == "Hello"
    assert conditional_pipeline(False) == "Goodbye World"


def test_pipe_with_partial_object_reference():
    add_partial = partial(lambda x, y: x + y, y=1)

    @pyped
    def partial_object_ref_pipeline(x):
        return x >> add_partial >> add_partial

    assert partial_object_ref_pipeline(5) == 7


def test_partial_application_pipeline():
    def multiply(x, y):
        return x * y

    double = partial(multiply, y=2)

    @pyped
    def partial_pipeline(x):
        return x >> double

    assert partial_pipeline(5) == 10


def test_pipe_with_default_argument_evaluation_time():
    eval_count = 0

    def default_value_func():
        nonlocal eval_count
        eval_count += 1
        return eval_count

    @pyped
    def default_eval_time_pipeline(x=default_value_func()):
        return x >> (lambda val: val)

    assert default_eval_time_pipeline() == 1


def test_pipe_with_mutable_default_argument():
    @pyped
    def mutable_default_arg_pipeline():
        def func(val, mutable_list=[]):
            mutable_list.append(val)
            return val, mutable_list

        return 1 >> func >> func >> (lambda val, lst: lst)

    assert mutable_default_arg_pipeline() == [1, 1]


def test_namedtuple_lambda_unpacking():
    from collections import namedtuple

    Point = namedtuple("Point", ["x", "y"])

    @pyped
    def namedtuple_unpacking_pipeline():
        point = Point(3, 4)
        return point >> (lambda x, y: x + y)

    assert namedtuple_unpacking_pipeline() == 7


def test_namedtuple_inner_def_unpacking():
    from collections import namedtuple

    Point = namedtuple("Point", ["x", "y"])

    @pyped
    def namedtuple_unpacking_pipeline():
        def add(x, y):
            return x + y

        point = Point(3, 4)
        return point >> add

    assert namedtuple_unpacking_pipeline() == 7


def test_namedtuple_outer_def_unpacking():
    from collections import namedtuple

    Point = namedtuple("Point", ["x", "y"])

    def add(x, y):
        return x + y

    @pyped
    def namedtuple_unpacking_pipeline():
        point = Point(3, 4)
        return point >> add

    assert namedtuple_unpacking_pipeline() == 7
