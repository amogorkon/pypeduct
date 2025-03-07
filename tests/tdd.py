"""Test-driven development tests, expected to fail."""

from __future__ import annotations

import pytest

from pypeduct.exceptions import PipeTransformError
from pypeduct.pyping import pyped


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


def test_pipe_with_unbound_method_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    @pyped
    def unbound_method_ref_pipeline(x):
        return x >> Calculator.add_one >> Calculator.add_one

    assert unbound_method_ref_pipeline(5) == 7


def test_pipe_with_bound_method_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)

    @pyped
    def bound_method_ref_pipeline():  # Bound method reference
        return instance >> instance.add_one >> instance.add_one

    assert bound_method_ref_pipeline() == 7


def test_named_expression_in_nested_comprehensions_pipeline():
    @pyped
    def named_expression_nested_comprehension_pipeline():
        return [
            [j >> (incremented := lambda x: x + 1) >> incremented for j in range(i)]
            for i in range(3)
        ]

    assert named_expression_nested_comprehension_pipeline() == [
        [],
        [2],
        [2, 4],
    ]


def test_named_expression_in_set_comprehension_pipeline():
    @pyped
    def named_expression_set_pipeline():
        return {i >> (doubled := lambda x: x * 2) >> doubled for i in range(3)}

    assert named_expression_set_pipeline() == {0, 4, 8}


def test_pipe_with_custom_object_method_reference():
    class CustomObject:
        def __init__(self, value):
            self.value = value

        def increment(self, _):
            self.value += 1
            return self

    obj = CustomObject(10)

    @pyped
    def custom_object_method_ref_pipe():
        return obj >> CustomObject.increment >> CustomObject.increment

    assert custom_object_method_ref_pipe().value == 12


def test_named_expression_in_dict_comprehension_pipeline():
    @pyped
    def named_expression_dict_pipeline():
        return {i: i >> (doubled := lambda x: x * 2) >> doubled for i in range(3)}

    assert named_expression_dict_pipeline() == {0: 0, 1: 4, 2: 8}


def test_named_expression_in_generator_expression_pipeline():
    @pyped
    def named_expression_generator_pipeline():
        return sum(i >> (doubled := lambda x: x * 2) >> doubled for i in range(3))

    assert named_expression_generator_pipeline() == 12


def test_named_expression_in_nested_lambda_pipeline():
    @pyped
    def named_expression_nested_lambda_pipeline(x):
        return (
            x
            >> (
                lambda val: lambda v: v
                >> (incremented := lambda w: w + 1)
                >> incremented
            )()
        )

    assert named_expression_nested_lambda_pipeline(5) == 7


def test_named_expression_in_lambda_pipeline():
    @pyped
    def named_expression_in_lambda_pipeline(x):
        return x >> (lambda val: val >> (incremented := lambda v: v + 1) >> incremented)

    assert named_expression_in_lambda_pipeline(5) == 7


def test_named_expression_async_pipeline():
    import asyncio

    @pyped
    async def named_expression_async_pipeline(x):
        return (
            x
            >> (async_increment := lambda val: asyncio.sleep(0.01) or val + 1)
            >> async_increment
        )

    async def run_named_expression_async_pipeline():
        return await named_expression_async_pipeline(5)

    assert asyncio.run(run_named_expression_async_pipeline()) == 7


def test_named_expression_property_pipeline():
    class MyClass:
        def __init__(self, value):
            self._value = value

        @property
        @pyped
        def processed_value(self):
            return self._value >> (double_op := lambda val: val * 2) >> double_op

    instance = MyClass(5)
    assert instance.processed_value == 20


def test_named_expression_staticmethod_pipeline():
    class MathUtils:
        @staticmethod
        @pyped
        def process_value(x):
            return x >> (increment_op := lambda val: val + 1) >> increment_op

    assert MathUtils.process_value(5) == 7


def test_named_expression_class_method_pipeline():
    class Calculator:
        def __init__(self, value):
            self.value = value

        @classmethod
        @pyped
        def create_and_process(cls, initial_value):
            return (
                initial_value
                >> (create_instance := lambda val: cls(val))
                >> create_instance
                >> (get_value := lambda calc: calc.value)
                >> get_value
            )

    calc_instance = Calculator.create_and_process(5)
    assert calc_instance.value == 5


def test_named_expression_decorator_pipeline():
    def decorator_factory(factor):
        def decorator(func):
            def wrapper(val):
                return func(val) * factor

            return wrapper

        return decorator

    @pyped
    def named_expression_decorator_pipeline(x):
        @decorator_factory(2)
        def doubled(val):
            return val

        return x >> (decorated_op := doubled) >> decorated_op

    assert named_expression_decorator_pipeline(5) == 20


def test_named_expression_nested_scopes_pipeline():
    factor = 3

    def outer_func():
        @pyped
        def nested_named_expression_scopes_pipeline(x):
            local_factor = 2
            return (
                x
                >> (multiplier := lambda val: val * factor)
                >> multiplier
                >> (adder := lambda val: val + local_factor)
                >> adder
            )

        return nested_named_expression_scopes_pipeline

    nested_pipeline_func = outer_func()
    assert nested_pipeline_func(5) == 17


def test_named_expression_with_walrus_pipeline():
    @pyped
    def named_expression_walrus_pipeline(x):
        return (
            (initial_value := x)
            >> (incremented := lambda val: val + 1)
            >> incremented
            >> (doubled := lambda val: val * 2)
            >> doubled
            >> (result := lambda val: val + initial_value)
            >> result
        )

    assert named_expression_walrus_pipeline(5) == 31


def test_named_expression_reuse_pipeline():
    @pyped
    def named_expression_reuse_pipeline(x):
        incremented = lambda val: val + 1
        return x >> (inc_op := incremented) >> inc_op >> inc_op

    assert named_expression_reuse_pipeline(5) == 8


def test_pipe_with_lambda_returning_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one_method(self, x):
            return x + 1

    instance = Calculator(5)
    bound_method = instance.add_one_method

    @pyped
    def lambda_method_return_pipeline(instance):
        return instance >> (lambda val: bound_method) >> (lambda method: method(val))

    assert lambda_method_return_pipeline(instance) == 6


def test_pipe_with_lambda_returning_nested_function():
    def outer_func():
        def inner_func(x):
            return x + 1

        return inner_func

    increment_func = outer_func()

    @pyped
    def lambda_nested_func_return_pipeline(x):
        return (
            x >> (lambda val: increment_func) >> (lambda nested_func: nested_func(val))
        )

    assert lambda_nested_func_return_pipeline(5) == 6


def test_pipe_with_lambda_returning_user_defined_function():
    def add_one(x):
        return x + 1

    @pyped
    def lambda_user_func_return_pipeline(x):
        return x >> (lambda val: add_one) >> (lambda user_func: user_func(val))

    assert lambda_user_func_return_pipeline(5) == 6


def test_pipe_with_lambda_returning_staticmethod():
    class MathUtils:
        @staticmethod
        def increment(x):
            return x + 1

    @pyped
    def lambda_staticmethod_return_pipeline(x):
        return (
            x
            >> (lambda val: MathUtils.increment)
            >> (lambda staticmethod: staticmethod(val))
        )

    assert lambda_staticmethod_return_pipeline(5) == 6


def test_pipe_with_lambda_returning_classmethod():
    class Calculator:
        def __init__(self, value):
            self.value = value

        @classmethod
        def create_with_value(cls, value):
            return cls(value)

    @pyped
    def lambda_classmethod_return_pipeline(x):
        return (
            x
            >> (lambda val: Calculator.create_with_value)
            >> (lambda classmethod: classmethod(val))
            >> (lambda instance: instance.value)
        )

    assert lambda_classmethod_return_pipeline(5) == 5


def test_pipe_with_lambda_returning_builtin_function():
    @pyped
    def lambda_builtin_func_return_pipeline(x):
        return x >> (lambda val: str) >> (lambda builtin_func: builtin_func(val))

    assert lambda_builtin_func_return_pipeline(5) == "5"


def test_pipe_with_lambda_returning_zip_object():
    @pyped
    def lambda_zip_return_pipeline():
        return (
            5
            >> (lambda val: zip(range(val), range(val, val + 3)))
            >> (lambda zip_obj: list(zip_obj))
        )

    assert lambda_zip_return_pipeline() == [(0, 5), (1, 6), (2, 7), (3, 8), (4, 9)]


def test_pipe_with_deeply_nested_lambda():
    @pyped
    def deeply_nested_lambda_pipeline(x):
        pipeline = x
        for _ in range(500):  # Deeply nested lambdas
            pipeline = pipeline >> (lambda v: lambda w: w + 1)()
        return pipeline

    assert deeply_nested_lambda_pipeline(0) == 500


def test_pipe_with_complex_mutation_chain():
    class DataMutator:
        def __init__(self, data):
            self.data = data

        def add_one(self):
            self.data["value"] += 1
            return self

        def multiply_by_two(self):
            self.data["value"] *= 2
            return self

        def get_value(self):
            return self.data["value"]

        def mutate_chain(self, data):
            return (
                data
                >> self.add_one()
                >> self.multiply_by_two()
                >> self.add_one()
                >> self.get_value()
            )

    mutator_instance = DataMutator({"value": 5})

    @pyped
    def complex_mutation_chain_pipeline(mutator):
        return mutator.mutate_chain({"value": 5})

    assert complex_mutation_chain_pipeline(mutator_instance) == 13, (
        "((5 + 1) * 2) + 1 == 13"
    )


def test_pipe_with_class_instance_mutation():
    class MutableData:
        def __init__(self, value):
            self.value = value

        def mutate(self):
            self.value += 1
            return self.value

    data_instance = MutableData(5)

    @pyped
    def class_instance_mutation_pipeline(data):
        return data >> (lambda obj: obj.mutate()) >> (lambda obj_val: obj_val)

    assert class_instance_mutation_pipeline(data_instance) == 7


def test_pipe_with_lambda_mutation():
    @pyped
    def lambda_mutation_pipeline(x):
        mutable_data = {"value": x}

        def mutate_lambda(data):
            data["value"] += 1
            return data["value"]

        return mutable_data >> mutate_lambda >> mutate_lambda

    assert lambda_mutation_pipeline(5) == 7


def test_pipe_with_closure_modification():
    def create_counter():
        count = 0

        def increment():
            nonlocal count
            count += 1
            return count

        @pyped
        def get_count_pipeline():
            return 5 >> (lambda x: increment())

        return get_count_pipeline, increment

    get_pipeline, incrementor = create_counter()

    def closure_modification_pipeline():
        count1 = get_pipeline()
        count2 = get_pipeline()
        incrementor()
        count3 = get_pipeline()
        return count1, count2, count3

    c1, c2, c3 = closure_modification_pipeline()
    assert (c1, c2, c3) == (1, 2, 4)


def test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10

        @pyped
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var
            nonlocal_var += 1
            return x >> (lambda val: val + nonlocal_var)

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert nonlocal_keyword_pipeline_func(5) == 16

    @pyped
    def closure_modification_pipeline():
        count1 = get_pipeline()
        count2 = get_pipeline()
        incrementor()
        count3 = get_pipeline()
        return count1, count2, count3

    c1, c2, c3 = closure_modification_pipeline()
    assert (c1, c2, c3) == (1, 2, 4)


def test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10

        @pyped
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var
            nonlocal_var += 1
            return x >> (lambda val: val + nonlocal_var)

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert nonlocal_keyword_pipeline_func(5) == 16


def test_pipe_with_lambda_argument_shadowing():
    factor = 10

    @pyped
    def lambda_arg_shadowing_pipeline(x):
        return x >> (lambda factor: lambda val: val * factor)(2)

    assert (
        lambda_arg_shadowing_pipeline(5) == 10
    )  # Lambda arg shadowing test, lambda factor (2) should be used, 5 * 2 = 10


def test_pipe_with_method_assignment():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def increment_method(self, x):
            return x + 1

    instance = Calculator(5)
    increment = instance.increment_method

    @pyped
    def method_assignment_pipeline(instance):
        return instance >> increment

    assert method_assignment_pipeline(instance) == 6


def test_pipe_with_nested_class_pipeline():
    class OuterClass:
        class InnerClass:  # Nested class
            def process(self, x):
                return x + 1

        def __init__(self):
            self.inner = OuterClass.InnerClass()

        @pyped
        def outer_method(self, x):
            return x >> self.inner.process

    outer_instance = OuterClass()

    @pyped
    def nested_class_pipeline(outer_instance):
        return outer_instance >> outer_instance.outer_method

    assert nested_class_pipeline(outer_instance) == 6


def test_pipe_with_instance_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)

    @pyped
    def instance_method_pipeline(instance):
        return instance >> instance.add_one

    assert instance_method_pipeline(instance) == 6


def test_pipe_with_unbound_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    unbound_method = Calculator.add_one

    @pyped
    def unbound_method_pipeline(x):
        return x >> unbound_method(Calculator(x))

    assert unbound_method_pipeline(5) == 6


def test_pipe_with_bound_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)
    bound_method = instance.add_one

    @pyped
    def bound_method_pipeline(instance):
        return instance >> bound_method

    assert bound_method_pipeline(instance) == 6


def test_pipe_with_partial_method():
    from functools import partial

    class Calculator:
        def __init__(self, value):
            self.value = value

        def add(self, amount):
            return Calculator(self.value + amount)

    calc_instance = Calculator(5)
    add_5_partial = partial(Calculator.add, calc_instance, 5)

    @pyped
    def partial_method_pipeline(calc):
        return calc >> add_5_partial >> (lambda c: c.value)

    assert partial_method_pipeline(calc_instance) == 10


def test_pipe_with_complex_default_expression():
    complex_default = [x * 2 for x in range(3)]  # Complex default expression

    @pyped
    def complex_default_expr_pipeline(x=complex_default):
        return x >> (lambda val: val)

    assert complex_default_expr_pipeline() == [0, 2, 4]


def test_pipe_with_default_argument_evaluation_time():
    eval_count = 0

    def default_value_func():
        nonlocal eval_count
        eval_count += 1
        return eval_count

    @pyped
    def default_eval_time_pipeline(
        x=default_value_func(),
    ):  # Default value evaluated at definition time, not call time
        return x >> (lambda val: val)

    assert default_eval_time_pipeline() == 1


def test_pipe_with_mutable_default_argument():
    @pyped
    def mutable_default_arg_pipeline():
        def func(val, mutable_list=[]):
            mutable_list.append(val)
            return mutable_list

        return 1 >> func >> func >> (lambda lst: lst)

    assert mutable_default_arg_pipeline() == [1, 1]


def test_pipe_with_loop_variable_capture():
    @pyped
    def loop_variable_capture_pipeline():
        funcs = []
        for i in range(3):
            funcs.append(lambda x: x + i)  # Capture loop variable i in lambda
        pipeline = 0
        for func in funcs:
            pipeline = pipeline >> func
        return pipeline

    assert loop_variable_capture_pipeline() == 3


def test_pipe_with_recursion_in_lambda_handling():
    @pyped
    def recursion_lambda_error_pipeline(n):
        return n >> (
            lambda x: (lambda f: lambda y: f(f)(y))(
                lambda rec: lambda val: rec(rec)(val + 1) if val < 1000 else val
            )
        )

    with pytest.raises(RecursionError):
        recursion_lambda_error_pipeline(0)


def test_pipe_with_overflow_in_lambda_handling():
    @pyped
    def overflow_lambda_pipeline():
        return 2**1000 >> (lambda x: x * 2**1000)

    # OverflowError is not consistently raised, might need to adjust by platform
    with pytest.raises(OverflowError):
        overflow_lambda_pipeline()


def test_pipe_with_recursion_error_handling():
    def recursive_func(n):
        return n >> (lambda x: recursive_func(x + 1)) if n < 1000 else n

    @pyped
    def recursion_error_pipeline():
        return 0 >> recursive_func

    with pytest.raises(RecursionError):
        recursion_error_pipeline()


def test_pipe_with_overflow_error_handling():
    @pyped
    def overflow_error_pipeline():
        return 2**1000 >> (lambda x: x * 2**1000)

    # OverflowError is not consistently raised in Python, might need to adjust platform-dependant
    with pytest.raises(OverflowError):
        overflow_error_pipeline()


def test_pipe_with_method_as_callable():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)

    @pyped
    def method_callable_pipeline(instance):
        return instance >> instance.add_one

    assert method_callable_pipeline(instance) == 6


def test_pipe_with_recursive_lambda():
    @pyped
    def recursive_lambda_pipeline(n):
        fact = lambda f: lambda x: f(f)(x) if x else 1
        factorial = fact(fact)
        return n >> factorial

    assert recursive_lambda_pipeline(5) == 120


def test_pipe_with_complex_class_pipeline():
    class DataProcessor:
        def __init__(self, data):
            self.data = data

        def filter_data(self, condition):
            return DataProcessor(list(filter(condition, self.data)))

        def sort_data(self):
            return DataProcessor(sorted(self.data))

        def get_average(self):
            if not self.data:
                return 0
            return sum(self.data) / len(self.data)

        def process_data(self, data, condition):
            return (
                data
                >> self.filter_data(condition)
                >> self.sort_data()
                >> self.get_average()
            )

    processor = DataProcessor([3, 1, 4, 1, 5, 9, 2, 6])

    @pyped
    def complex_class_pipeline(processor, condition):
        return processor.process_data([3, 1, 4, 1, 5, 9, 2, 6], condition)

    assert complex_class_pipeline(processor, lambda x: x > 3) == 6.0


def test_deeply_nested_pipeline():
    @pyped
    def deeply_nested_pipeline(x):
        pipeline = x
        for _ in range(500):
            pipeline = pipeline >> (lambda v: lambda w: w + 1)()
        return pipeline

    assert deeply_nested_pipeline(0) == 500


def test_lambda_with_kwargs_in_pipeline():
    @pyped
    def lambda_kwargs_pipeline(x, **kwargs):
        return x >> (lambda val, **kwargs: val + kwargs["inc"])

    assert lambda_kwargs_pipeline(5, inc=1) == 6


def test_with_statement_in_pipeline():
    class ContextManager:
        def __enter__(self):
            print("Entering context")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("Exiting context")

        def process(self, x):
            return x >> (lambda val: val + 1)

    @pyped
    def with_statement_pipeline(x):
        with ContextManager() as cm:
            return x >> cm.process

    assert with_statement_pipeline(5) == 6


def test_nested_class_transformation():
    @pyped(verbose=True)
    class Outer:
        class Inner:
            def process(self, x: int) -> int:
                return x >> (lambda y: y * 3)

    instance = Outer.Inner()
    assert instance.process(2) == 6, "Nested class method not transformed!"


def test_inheritance():
    @pyped
    class Base:
        def process(self, x: int) -> int:
            return x >> (lambda y: y + 1)

    class Child(Base):
        def process(self, x: int) -> int:
            return super().process(x) >> (lambda y: y * 2)

    assert Child().process(3) == (3 + 1) * 2, "Inheritance broken!"
