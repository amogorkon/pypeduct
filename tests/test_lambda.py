from __future__ import annotations

from pypeduct import pyped


def test_simple_pipeline():
    @pyped
    def simple_pipeline(x: int) -> int:
        return x >> (lambda y: y + 1)

    assert simple_pipeline(2) == 3


def test_pipe_with_lambda_returning_tuple():
    @pyped
    def lambda_tuple_return_pipeline(x):
        return x >> (lambda val: (val + 1, val * 2))

    assert lambda_tuple_return_pipeline(5) == (6, 10)


def test_lambda_with_defaults_in_pipeline():
    @pyped
    def lambda_defaults_pipeline(x):
        return x >> (lambda val, inc=1: val + inc)

    assert lambda_defaults_pipeline(5) == 6


def test_nested_pipelines():
    @pyped
    def nested_pipeline(x: int) -> int:
        return x >> (lambda val: val + 1 >> (lambda v: v * 2))

    assert nested_pipeline(5) == 12  # 5 + 1 = 6, 6 * 2 = 12


def test_pipe_with_lambda_returning_list():
    @pyped
    def lambda_list_return_pipeline(x):
        return x >> (lambda val: [val + 1, val * 2])

    assert lambda_list_return_pipeline(5) == [6, 10]


def test_pipe_with_lambda_returning_dict():
    @pyped
    def lambda_dict_return_pipeline(x):
        return x >> (lambda val: {"incremented": val + 1, "doubled": val * 2})

    assert lambda_dict_return_pipeline(5) == {
        "incremented": 6,
        "doubled": 10,
    }  # Lambda returning dict


def test_pipe_with_lambda_returning_set():
    @pyped
    def lambda_set_return_pipeline(x):
        return x >> (lambda val: {val, val + 1, val * 2})

    assert lambda_set_return_pipeline(5) == {5, 6, 10}  # Lambda returning set


def test_pipe_with_lambda_returning_frozenset():
    @pyped
    def lambda_frozenset_return_pipeline(x):
        return x >> (lambda val: frozenset({val, val + 1, val * 2}))

    assert lambda_frozenset_return_pipeline(5) == frozenset({
        5,
        6,
        10,
    })  # Lambda returning frozenset


def test_pipe_with_lambda_returning_generator():
    @pyped
    def lambda_generator_return_pipeline(x):
        return (
            x
            >> (lambda val: (i for i in range(val, val + 3)))
            >> (lambda gen: list(gen))
        )

    assert lambda_generator_return_pipeline(5) == [
        5,
        6,
        7,
    ]  # Lambda returning generator


def test_pipe_with_lambda_returning_map_object():
    @pyped
    def lambda_map_return_pipeline(x):
        return (
            x
            >> (lambda val: map(lambda i: i * 2, range(val, val + 3)))
            >> (lambda map_obj: list(map_obj))
        )

    assert lambda_map_return_pipeline(5) == [10, 12, 14]  # Lambda returning map object


def test_pipe_with_lambda_returning_filter_object():
    @pyped
    def lambda_filter_return_pipeline(x):
        return (
            x
            >> (lambda val: filter(lambda i: i % 2 == 0, range(val, val + 5)))
            >> (lambda filter_obj: list(filter_obj))
        )

    assert lambda_filter_return_pipeline(5) == [6, 8]  # Lambda returning filter object


def test_pipe_with_lambda_returning_enumerate_object():
    @pyped
    def lambda_enumerate_return_pipeline(x):
        return (
            x
            >> (lambda val: enumerate(range(val, val + 3)))
            >> (lambda enum_obj: [(index, value) for index, value in enum_obj])
        )

    assert lambda_enumerate_return_pipeline(5) == [
        (0, 5),
        (1, 6),
        (2, 7),
    ]  # Lambda returning enumerate object


def test_pipe_with_lambda_returning_reversed_object():
    @pyped
    def lambda_reversed_return_pipeline(x):
        return (
            x
            >> (lambda val: reversed(range(val, val + 3)))
            >> (lambda reversed_obj: list(reversed_obj))
        )

    assert lambda_reversed_return_pipeline(5) == [
        7,
        6,
        5,
    ]  # Lambda returning reversed object


def test_pipe_with_lambda_returning_memoryview_object():
    @pyped
    def lambda_memoryview_return_pipeline(x):
        return (
            x
            >> (lambda val: memoryview(b"hello"))
            >> (lambda mem_obj: mem_obj.tobytes())
        )

    assert (
        lambda_memoryview_return_pipeline(5) == b"hello"
    )  # Lambda returning memoryview object


def test_pipe_with_lambda_returning_class_instance():
    class MyClass:
        def __init__(self, value):
            self.value = value

    @pyped
    def lambda_class_instance_return_pipeline(x):
        return x >> (lambda val: MyClass(val)) >> (lambda instance: instance.value)

    assert (
        lambda_class_instance_return_pipeline(5) == 5
    )  # Lambda returning class instance


def test_pipe_with_lambda_returning_partial_object():
    from functools import partial

    add_partial = partial(lambda x, y: x + y, y=1)

    @pyped
    def lambda_partial_return_pipeline(x):
        return x >> (lambda val: add_partial) >> (lambda partial_obj: partial_obj(5))

    assert lambda_partial_return_pipeline(5) == 6


def test_pipe_with_lambda_returning_closure():
    def create_closure(factor):
        return lambda val: val * factor

    @pyped
    def lambda_closure_return_pipeline(x):
        return x >> (lambda val: create_closure(val)) >> (lambda closure: closure(2))

    assert lambda_closure_return_pipeline(5) == 10


def test_pipe_with_lambda_returning_binop_expression():
    @pyped
    def lambda_binop_return_pipeline(x):
        return x >> (lambda val: val + 1 * 2)

    assert lambda_binop_return_pipeline(5) == 7


def test_pipe_with_lambda_returning_list_comprehension():
    @pyped
    def lambda_list_comprehension_return_pipeline(x):
        return x >> (lambda val: [i * val for i in range(3)])

    assert lambda_list_comprehension_return_pipeline(5) == [0, 5, 10]


def test_pipe_with_lambda_returning_generator_expression():
    @pyped
    def lambda_generator_comprehension_return_pipeline(x):
        return (
            x >> (lambda val: (i * val for i in range(3))) >> (lambda gen: sum(gen))
        )  # Lambda returning generator expression

    assert (
        lambda_generator_comprehension_return_pipeline(5) == 15
    )  # Lambda returning generator expression


def test_pipe_with_lambda_returning_assignment_expression():
    @pyped
    def lambda_assignment_expression_return_pipeline(x):
        return x >> (lambda val: (y := val * 2))

    assert lambda_assignment_expression_return_pipeline(5) == 10


def test_pipe_with_lambda_returning_call_expression():
    def add_one(x):
        return x + 1

    @pyped
    def lambda_call_expression_return_pipeline(x):
        return x >> (lambda val: add_one(val))

    assert lambda_call_expression_return_pipeline(5) == 6


def test_pipe_with_lambda_returning_attribute_expression():
    class MyClass:
        def __init__(self, value):
            self.value = value

    instance = MyClass(7)

    @pyped
    def lambda_attribute_expression_return_pipeline(instance):
        return instance >> (lambda obj: obj.value)

    assert lambda_attribute_expression_return_pipeline(instance) == 7


def test_pipe_with_lambda_returning_subscript_expression():
    data = [10, 20, 30]

    @pyped
    def lambda_subscript_expression_return_pipeline(data):
        return data >> (lambda lst: lst[1])

    assert lambda_subscript_expression_return_pipeline(data) == 20


def test_pipe_with_lambda_returning_starred_expression():
    @pyped
    def lambda_starred_expression_return_pipeline(x):
        return x >> (lambda val: [*range(val, val + 3)])

    assert lambda_starred_expression_return_pipeline(5) == [5, 6, 7]


def test_lambda_with_kwargs_in_pipeline():
    @pyped
    def lambda_kwargs_pipeline(x, **kwargs):
        return x >> (lambda val: val + kwargs["inc"])

    assert lambda_kwargs_pipeline(5, inc=1) == 6


def test_lambda_with_varargs_in_pipeline():
    @pyped
    def lambda_varargs_pipeline(x):
        return x >> (lambda val, *args: val + sum(args))(1, 2, 3)

    assert lambda_varargs_pipeline(5) == 11


def test_lambda_no_args_with_input_pipe():
    @pyped
    def lambda_no_args_input_pipeline(x):
        return x >> (lambda _: 10)

    assert lambda_no_args_input_pipeline(5) == 10


def test_lambda_positional_only_args_pipe():
    @pyped
    def lambda_pos_only_pipeline(x):
        return x >> (lambda val, /, inc: val + inc)(inc=1)

    assert lambda_pos_only_pipeline(5) == 6


def test_lambda_keyword_only_args_pipe():
    @pyped
    def lambda_kw_only_pipeline(x):
        return x >> (lambda val, *, inc: val + inc)(inc=1)

    assert lambda_kw_only_pipeline(5) == 6


def test_lambda_mixed_args_complex_pipe():
    @pyped
    def lambda_mixed_complex_pipeline(x):
        return x >> (
            lambda pos_only, val, *, kw_only, **kwargs: pos_only
            + val
            + kw_only
            + sum(kwargs.values())
        )(1, kw_only=2, other=3, another=4)

    assert lambda_mixed_complex_pipeline(5) == 15


def test_lambda_in_pipeline():
    @pyped
    def lambda_pipeline(x):
        return x >> (lambda val: val * 2)

    assert lambda_pipeline(0) == 0
    assert lambda_pipeline(1) == 2


def test_lambda_capture_free_vars_pipe():
    factor = 3

    @pyped
    def capture_free_vars_pipeline(x):
        return x >> (lambda val: val * factor)

    assert capture_free_vars_pipeline(5) == 15


def test_lambda_closure_pipe():
    def create_multiplier(factor):
        return lambda val: val * factor

    multiplier = create_multiplier(3)

    @pyped
    def closure_pipeline(x):
        return x >> multiplier

    assert closure_pipeline(5) == 15


def test_pipe_with_lambda_returning_conditional_expression():
    @pyped
    def lambda_conditional_expression_return_pipeline(x):
        return x >> (lambda val: "Positive" if val > 0 else "Non-positive")

    assert lambda_conditional_expression_return_pipeline(5) == "Positive"


def test_pipe_with_lambda_function_reference():
    increment_lambda = lambda x: x + 1

    @pyped
    def lambda_func_ref_pipeline(x):
        return x >> increment_lambda >> increment_lambda

    assert lambda_func_ref_pipeline(5) == 7


def test_lambda_capture_free_vars_pipe():
    factor = 3

    @pyped
    def capture_free_vars_pipeline(x):
        return x >> (lambda val: val * factor)

    assert capture_free_vars_pipeline(5) == 15


def test_lambda_closure_pipe():
    def create_multiplier(factor):
        return lambda val: val * factor

    multiplier = create_multiplier(3)

    @pyped
    def closure_pipeline(x):
        return x >> multiplier

    assert closure_pipeline(5) == 15


def test_pipe_with_lambda_returning_lambda():
    @pyped
    def lambda_lambda_return_pipeline(x):
        return (
            x >> (lambda val: lambda v: v + 1) >> (lambda inner_lambda: inner_lambda(5))
        )

    assert lambda_lambda_return_pipeline(5) == 6


def test_pipe_with_lambda_returning_nested_function():
    def outer_func(y):
        def inner_func(x):
            return x + y

        return inner_func

    increment_func = outer_func(1)

    @pyped
    def lambda_nested_func_return_pipeline(x):
        return x >> (val := increment_func) >> (lambda x: outer_func(val)(x))

    assert lambda_nested_func_return_pipeline(5) == 12, "val = (5 + 1); val + val = 12"


def test_pipe_with_lambda_returning_zip_object():
    @pyped
    def lambda_zip_return_pipeline():
        return 5 >> (lambda val: zip(range(val), range(val, val + 3))) >> list

    assert lambda_zip_return_pipeline() == [(0, 5), (1, 6), (2, 7)]


def test_pipe_with_lambda_argument_shadowing():
    factor = 10

    @pyped
    def lambda_arg_shadowing_pipeline(x):
        return x >> (lambda val, factor: val * factor)(2)

    # Lambda arg shadowing test, lambda factor (2) should be used, 5 * 2 = 10
    assert lambda_arg_shadowing_pipeline(5) == 10


def test_pipe_y_combinator():
    @pyped
    def recursive_lambda_pipeline(n):
        fact = lambda f: lambda x: x * f(f)(x - 1) if x > 0 else 1
        factorial = fact(fact)
        return n >> factorial

    assert recursive_lambda_pipeline(5) == 120
