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
    def exception_pipe():
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
    def exception_in_function():
        def faulty_function(x: int):
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
    result = 5 >>
    return result
"""
    with pytest.raises(SyntaxError) as context:
        exec(faulty_code, globals())

    assert "invalid syntax" in str(context.value)


def test_pipe_with_class_method_inside():
    class MyClass:
        def __init__(self, value):
            self.value = value

        @pyped
        def multiply(self, x: int) -> int:
            return x >> (lambda y: y * self.value)

    instance = MyClass(3)

    result = instance.multiply(5)
    assert result == 15


def test_pipe_with_method_inside():
    class MyClass:
        def __init__(self, value):
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
        def __init__(self, value):
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
    def partial_func_pipe():
        def multiply(a, b):
            return a * b

        multiply_by_two = partial(multiply, b=2)
        result = 5 >> multiply_by_two
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
        def __init__(self, value):
            self.value = value

        def foo(self, x):
            return x.value + self.value

    @pyped
    def custom_object_pipe():
        obj = CustomObject(10)
        return obj >> obj.foo

    assert custom_object_pipe() == 20
