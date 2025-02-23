import asyncio

import pytest

from pypeduct.pyping import pyped


def test_basic_pipe():
    @pyped
    def basic_pipe() -> list[str]:
        result = 5 >> str << list
        return result

    assert basic_pipe() == ["5"]


def test_async_pipe():
    @pyped
    async def async_func() -> int:
        return 10 >> (lambda x: x * 2)

    result = asyncio.run(async_func())
    assert result == 20


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
        def wrap(text):
            return f"<{text}>"

        result = "content" >> wrap
        return result

    assert rshift_pipe() == "<content>"


def test_nested_pyped():
    @pyped
    def nested_pyped() -> int:
        result = (5 >> (lambda x: x + 2)) >> (lambda x: x * 3)
        return result

    assert nested_pyped() == 21


def test_complex_expression_pipe():
    @pyped
    def complex_expression_pipe() -> int:
        expr = (2 + 3) * 4
        result = expr >> (lambda x: x - 5)
        return result

    assert complex_expression_pipe() == 15


def test_await_in_pipe():
    @pyped
    async def await_pipe() -> str:
        async def async_upper(s):
            await asyncio.sleep(0.1)
            return s.upper()

        return await ("hello" >> async_upper)

    result = asyncio.run(await_pipe())
    assert result == "HELLO"


def test_exception_handling_in_pipe():
    @pyped
    def exception_pipe():
        result = "test" >> int  # This should raise a ValueError
        return result

    with pytest.raises(ValueError):
        exception_pipe()


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


def test_pipe_with_generator_expression():
    @pyped
    def generator_pipe():
        def square(x):
            return x * x

        gen = (i for i in range(5))
        result = list(gen) >> (lambda lst: [square(x) for x in lst])
        return result

    assert generator_pipe() == [0, 1, 4, 9, 16]


def test_variable_scope_in_exec():
    @pyped
    def context_test():
        var = "hello"
        result = var >> str.upper
        return result

    assert context_test() == "HELLO"


def test_pipe_with_lambda():
    @pyped
    def lambda_test():
        result = 5 >> (lambda x: x * x)
        return result

    assert lambda_test() == 25


def test_pipe_with_async_generator():
    @pyped
    async def async_generator_pipe():
        async def async_gen():
            for i in range(3):
                yield i

        result = [i async for i in async_gen()] >> list
        return result

    result = asyncio.run(async_generator_pipe())
    assert result == [0, 1, 2]


def test_pipe_with_exception_in_function():
    @pyped
    def exception_in_function():
        def faulty_function(x):
            raise ValueError("Test exception")

        result = 5 >> faulty_function
        return result

    with pytest.raises(ValueError):
        exception_in_function()


def test_pipe_with_none():
    @pyped
    def none_pipe():
        result = None >> (lambda x: x is None)
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
    def kwargs_function():
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        result = "Alyz" << greet(greeting="Hi")
        assert result == "Alyz" >> greet(greeting="Hi")
        return result

    assert kwargs_function() == "Hi, Alyz!"


def test_pipe_with_multiple_pyped_in_one_expression():
    @pyped
    def multiple_pyped():
        result = 5 >> (lambda x: x + 1) >> (lambda x: x * 2) << (lambda x: x - 3)
        return result

    assert multiple_pyped() == 9


def test_pipe_with_unary_operator():
    @pyped
    def unary_operator_test():
        result = (-5) >> abs
        return result

    assert unary_operator_test() == 5


def test_pipe_with_chained_comparisons():
    @pyped
    def chained_comparison_test(x: int) -> bool:
        return (1 < x < 10) >> (lambda x: x)

    assert chained_comparison_test(5)
    assert not chained_comparison_test(0)
