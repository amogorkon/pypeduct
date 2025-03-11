from __future__ import annotations

import pytest

from pypeduct import pyped


def test_exception_handling_pipe():
    def error_func(x):
        raise ValueError("Test Exception")

    @pyped
    def exception_pipeline(x):
        try:
            return x >> error_func
        except ValueError as e:
            return str(e)

    assert exception_pipeline(5) == "Test Exception"


def test_nested_exception_handling_pipe():
    def inner_error_func(x):
        raise TypeError("Inner Exception")

    def outer_func(x):
        try:
            return x >> inner_error_func
        except TypeError as e:
            raise ValueError("Outer Exception") from e

    @pyped
    def nested_exception_pipeline(x):
        try:
            return x >> outer_func
        except ValueError as e:
            return str(e)

    assert nested_exception_pipeline(5) == "Outer Exception"  # Catches outer exception


def test_pipe_with_type_error_handling():
    @pyped
    def type_error_pipeline():
        return "hello" >> (
            lambda x: 1 / x
        )  # Division by string - should raise TypeError

    with pytest.raises(TypeError):
        type_error_pipeline()  # Expect TypeError to be raised


def test_pipe_with_value_error_handling():
    import math

    @pyped
    def value_error_pipeline():
        return -1 >> (lambda x: math.sqrt(x))

    with pytest.raises(ValueError):
        value_error_pipeline()


def test_pipe_with_index_error_handling():
    @pyped
    def index_error_pipeline():
        return [] >> (
            lambda x: x[0]
        )  # Accessing index 0 of empty list - should raise IndexError

    with pytest.raises(IndexError):
        index_error_pipeline()  # Expect IndexError to be raised


def test_pipe_with_key_error_handling():
    @pyped
    def key_error_pipeline():
        return {} >> (
            lambda x: x["key"]
        )  # Accessing non-existent key in dict - should raise KeyError

    with pytest.raises(KeyError):
        key_error_pipeline()  # Expect KeyError to be raised


def test_pipe_with_attribute_error_handling():
    class MyClass:
        pass

    instance = MyClass()

    @pyped
    def attribute_error_pipeline(instance):
        return instance >> (
            lambda x: x.non_existent_attribute
        )  # Accessing non-existent attribute - should raise AttributeError

    with pytest.raises(AttributeError):
        attribute_error_pipeline(instance)  # Expect AttributeError to be raised


def test_pipe_with_zero_division_error_handling():
    @pyped
    def zero_division_pipeline():
        return 1 >> (
            lambda x: x / 0
        )  # Division by zero - should raise ZeroDivisionError

    with pytest.raises(ZeroDivisionError):
        zero_division_pipeline()  # Expect ZeroDivisionError to be raised


def test_pipe_with_overflow_error_handling():
    @pyped
    def overflow_error_pipeline():
        return 2.0**1000 >> (lambda x: x**1000)

    # OverflowError is not consistently raised in Python, might need to adjust expectation
    with pytest.raises(OverflowError):
        overflow_error_pipeline()


def test_pipe_with_recursion_error_handling():
    @pyped
    def recursive_func(n):
        return n >> (lambda x: recursive_func(x + 1)) if n < 1000 else n

    @pyped
    def recursion_error_pipeline():
        return 0 >> recursive_func

    with pytest.raises(RecursionError):
        recursion_error_pipeline()


def test_pipe_with_syntax_error_handling():
    @pyped
    def syntax_error_pipeline():
        return 5 >> (lambda x: eval("syntax error"))

    with pytest.raises(SyntaxError):
        syntax_error_pipeline()


def test_pipe_with_unicode_decode_error_handling():
    @pyped
    def unicode_decode_error_pipeline():
        return b"\xc2\x00" >> (lambda x: x.decode("utf-8"))

    with pytest.raises(UnicodeDecodeError):
        unicode_decode_error_pipeline()


def test_pipe_with_unicode_encode_error_handling():
    @pyped
    def unicode_encode_error_pipeline():
        return "€" >> (lambda x: x.encode("ascii"))

    with pytest.raises(UnicodeEncodeError):
        unicode_encode_error_pipeline()


def test_pipe_with_generator_exit_handling():
    def generator_with_exit():
        try:
            yield 1
            yield 2
        except GeneratorExit:
            print(
                "Generator exited"
            )  # To show GeneratorExit handling, if test runner captures stdout
            raise
        finally:
            print(
                "Generator finally"
            )  # To show finally block execution, if test runner captures stdout

    @pyped
    def generator_exit_pipeline():
        gen = generator_with_exit()
        next(gen)
        gen.close()
        return 5 >> (lambda x: "Generator closed")

    assert generator_exit_pipeline() == "Generator closed"


def test_pipe_with_system_exit_handling():
    @pyped
    def system_exit_pipeline():
        return 5 >> (lambda x: exit(0))  # Call to exit - should raise SystemExit

    # SystemExit is special, might not be caught by try/except in pyped.
    with pytest.raises(SystemExit):
        system_exit_pipeline()  # Expect SystemExit to be raised, might terminate test run


def test_pipe_with_generator_return_handling():
    # sourcery skip: remove-unreachable-code
    def generator_with_return():
        yield 1
        return "Generator return value"
        yield 2  # Unreachable

    @pyped
    def generator_return_pipeline():
        gen = generator_with_return()
        return gen >> (lambda x: list(x))

    assert generator_return_pipeline() == [1]


def test_pipe_with_stop_iteration_handling():
    class MyIterator:
        def __iter__(self):
            return self

        def __next__(self):
            raise StopIteration

    @pyped
    def stop_iteration_pipeline():
        return MyIterator() >> (lambda x: list(x))

    assert stop_iteration_pipeline() == []


def test_pipe_with_name_error_handling():
    @pyped
    def name_error_pipeline():
        return non_existent_name >> (lambda x: x)

    with pytest.raises(NameError):
        name_error_pipeline()


def test_custom_exception_message():
    faulty_code = """
@pyped
def invalid_syntax():
    return return
"""
    with pytest.raises(SyntaxError):
        exec(faulty_code, globals())


def test_pipe_with_recursive_lambda():
    @pyped
    def recursive_lambda_pipeline(n):
        fact = lambda f: lambda x: f(f)(x) if x else 1
        factorial = fact(fact)
        return n >> factorial

    with pytest.raises(RecursionError):
        recursive_lambda_pipeline(5)
