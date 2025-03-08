from math import hypot

import pytest

from pypeduct import PipeTransformError, pyped


def test_tuple_unpacking_lambda():
    @pyped
    def multiple_assignments() -> int:
        return (1, 2) >> (lambda x, y: x + y)

    assert multiple_assignments() == 3


def test_tuple_unpacking_function():
    @pyped
    def multiple_assignments() -> tuple[int, int]:
        def add(x: int, y: int) -> int:
            return x + y

        return (1, 2) >> add

    assert multiple_assignments() == 3


def test_pipe_with_tuple_concat():
    @pyped
    def tuple_concat_pipeline():
        return (1, 2) >> (lambda x: x + (3, 4))

    assert tuple_concat_pipeline() == (1, 2, 3, 4)


def test_pipe_with_tuple_literal():
    @pyped
    def tuple_literal_pipeline():
        return (1, 2, 3) >> (lambda x: sum(x))

    assert tuple_literal_pipeline() == 6


def test_keyword_args_pipeline():
    @pyped
    def keyword_args_pipeline(x):
        return x >> (lambda val, factor=2: val * factor)

    assert keyword_args_pipeline(5) == 10  # 5 * 2 = 10


def test_tuple_unpacking_pipe():
    def add(x: int, y: int) -> int:
        return x + y

    def multiply_and_add(x: int, y: int) -> int:
        return x * y, x + y

    @pyped
    def multiple_assignments() -> int:
        return (1, 2) >> multiply_and_add >> add

    assert multiple_assignments() == 5  # (1*2), (1+2) => 2, 3 => 2 + 3 => 5


def test_tuple_not_unpacked():
    @pyped
    def multiple_assignments() -> int:
        return (1, 2) >> (lambda x: x + 1)

    with pytest.raises(TypeError):
        multiple_assignments()


def test_tuple_unpacking_failure():
    @pyped
    def multiple_assignments() -> int:
        return (1, 2) >> (lambda x, y, z: x + 1)

    with pytest.raises(TypeError):
        multiple_assignments()


def test_tuple_with_default_args():
    @pyped
    def test_default_args() -> int:
        def add(x: int, y: int = 0) -> int:
            return x + y

        return (1,) >> add

    assert test_default_args() == 1


def test_no_unpacking_to_sequence():
    def pipe(X: list[int] = None, y=0):
        for x in X:  # sourcery skip: no-loop-in-tests
            yield x * y

    @pyped
    def test1():
        return [1, 2] >> pipe >> list

    assert test1() == [0, 0]

    @pyped
    def test2():
        return [1, 2] >> pipe(y=2) >> list

    assert test2() == [2, 4]


def test_variadic_function():
    @pyped
    def test_variadic() -> int:
        def sum_all(*args: int) -> int:
            return sum(args)

        return (1, 2, 3) >> sum_all  # Should pass args as (1, 2, 3) => 6

    assert test_variadic() == 6


def test_variadic_function_single_value():
    def collect_args(*args):
        return args

    @pyped
    def test():
        # Single value should still be treated as a tuple as the function is variadic
        return 42 >> collect_args

    assert test() == (42,)


def test_variadic_function_with_keyword():
    def multiply_and_sum(multiplier, *args, offset=0):
        return (multiplier * sum(args)) + offset  # Apply offset after multiplication

    @pyped
    def test():
        return 2 >> multiply_and_sum(3, 4, 5, offset=10)

    assert test() == 34


def test_variadic_function_with_default():
    def multiply_and_sum(multiplier, *args, offset=10):  # Default offset to 10
        return (multiplier * sum(args)) + offset

    @pyped
    def test():
        return 2 >> multiply_and_sum(3, 4, 5)  # No explicit offset

    assert test() == 34


def test_variadic_function_empty_args_with_keyword():
    def multiply_and_sum(multiplier, *args, offset=10):
        return (multiplier * (sum(args) if args else 1)) + offset  # Handle empty *args

    @pyped
    def test():
        return 2 >> multiply_and_sum(offset=5)  # No extra arguments

    assert test() == 7


# Callable class
class AdderUnpack:
    def __call__(self, a: int, b: int) -> int:
        return a + b


class AdderVariadic:
    def __call__(self, *args: int) -> int:
        return sum(args)


def test_callable_class():
    @pyped
    def test_callable() -> int:
        adder = AdderUnpack()
        return (1, 2) >> adder

    assert test_callable() == 3


def test_callable_class_variadic():
    @pyped
    def test_callable() -> int:
        adder = AdderVariadic()
        return (1, 2, 3) >> adder

    assert test_callable() == 6


def test_callable_external_def():
    @pyped
    def test_callable() -> float:
        return (3, 4) >> hypot

    assert test_callable() == 5


def variadic_function(*args: int) -> int:
    return sum(args)


def test_callable_external_def_variadic():
    @pyped
    def test_callable() -> int:
        return (1, 2, 3) >> variadic_function

    assert test_callable() == 6


# --------------------------------------------------
# Valid placeholder usage tests
# --------------------------------------------------
def test_positional_placeholder():
    @pyped()
    def test():
        return (5, 6) >> (lambda a, b: a + b)(..., (10,))

    assert test() == (5, 6, 10)


def test_keyword_placeholder():
    @pyped()
    def test():
        return {"x": 2, "y": 3} >> (lambda z=10, d=None: z + d["y"])(d=...)

    assert test() == 13  # y=3 (from dict) + 10 (from lambda)


def test_mixed_positional_keyword_placeholder():
    @pyped()
    def test():
        return [10, 20] >> (lambda a, b: a * b)(..., 2)

    assert test() == [10, 20, 10, 20]  # [10,20] * 2


def test_mixed_positional_keywords_no_placeholder():
    @pyped()
    def test():
        return (3, 4) >> (lambda a, b=10: a + b)

    assert test() == 7  # 3 + 4


# --------------------------------------------------
# Error case tests
# --------------------------------------------------
def test_multiple_placeholders_error():
    with pytest.raises(PipeTransformError) as exc:

        @pyped()
        def test():
            return 5 >> (lambda a, b: a + b)(..., ...)

        test()

    assert "Only one argument position placeholder" in str(exc.value)


def test_left_side_placeholder_error():
    with pytest.raises(PipeTransformError) as exc:

        @pyped()
        def test():
            return ... >> (lambda x: x + 1)

        test()

    assert "left side of the pipe" in str(exc.value)


def test_placeholder_override_annotation():
    @pyped()
    def test():
        def func(items: list[int] = None, foo=None):
            return items, sum(foo)

        return (1, 2, 3) >> func(foo=...)  # Should pass tuple directly

    assert test() == (None, 6)  # sum((1,2,3)) not sum(1,2,3)


# --------------------------------------------------
# Edge case tests
# --------------------------------------------------
def test_placeholder_with_starred_args():
    @pyped()
    def test():
        return (1, 2) >> (lambda *args: sum(args))(...)

    with pytest.raises(TypeError):
        test()  # sum((1,2)) will error but shows proper transformation as ... is not unpacked


def test_placeholder_in_nested_call():
    @pyped
    def test():
        return 5 >> (lambda x: x + 1)((lambda y: y * 2)(...))

    with pytest.raises(TypeError):
        test()  # considering that partials are the default in pypelines, this is only logical.
        # The ... is passed in as argument into a partial function => ... * 2 = ??


def test_placeholder_with_unpacking_override():
    @pyped()
    def test():
        def func(a, b):
            return a + b

        return (5, 5) >> func(..., 10)  # Should pass tuple to first arg

    with pytest.raises(TypeError):
        test()  # func((5,5), 10) will error but shows proper transformation
