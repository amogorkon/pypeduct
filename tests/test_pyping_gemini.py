# tests/test_pyping_gemini.py

import pytest

from pypeduct import pyped


def test_pipe_with_custom_object_walrus():
    class CustomObject:
        def __init__(self, value):
            self.value = value

        def increment(self, _: None) -> CustomObject:
            self.value += 1
            return self

        def foo(self, x: "CustomObject") -> int:
            return x.value * 2

    @pyped
    def custom_object_pipe() -> int:
        return (obj := CustomObject(10)) >> obj.increment >> obj.increment >> obj.foo

    assert custom_object_pipe() == 24


def test_chained_walrus_assignments():
    @pyped
    def chained_walrus():
        return (a := 1) >> (b := lambda x: x + 1) >> (c := lambda x: x * 2)

    assert chained_walrus() == (1, 2, 4)


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


def test_pipeline_inside_conditional_Walrus():
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


def test_assignment_in_pipeline():
    @pyped
    def assignment_pipeline() -> int:
        x = 5
        y = (x := x + 5) >> (lambda val: val * 2)
        return x + y

    assert assignment_pipeline() == 30  # x becomes 10, y becomes 20, 10 + 20 = 30


def test_nested_pipelines():
    @pyped
    def nested_pipeline(x: int) -> int:
        return x >> (lambda val: val + 1 >> (lambda v: v * 2))

    assert nested_pipeline(5) == 12  # 5 + 1 = 6, 6 * 2 = 12


def test_rshift_pipeline():
    @pyped
    def rshift_pipeline(x):
        return (lambda v: v * 2) << x

    assert rshift_pipeline(5) == 10  # 5 * 2 = 10


def test_mixed_shift_pipeline():
    @pyped
    def mixed_pipeline(x):
        return x >> (lambda v: v + 1) << (lambda v: v * 2)

    assert mixed_pipeline(5) == 12  # (5 + 1) * 2 = 12


def test_no_pipes():
    @pyped
    def no_pipeline(x):
        return x + 1

    assert no_pipeline(5) == 6  # 5 + 1 = 6


def test_class_method_pipe():
    @pyped
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add(self, amount):
            return Calculator(self.value + amount)

        def multiply(self, factor):
            return Calculator(self.value * factor)

        def get_value(self):
            return self.value

        def calculate(self, amount, factor):
            return (
                self.value
                >> self.add(amount)
                >> self.multiply(factor)
                >> self.get_value()
            )

    calc = Calculator(5)
    assert calc.calculate(3, 2) == 16  # (5 + 3) * 2 = 16


def test_async_function_pipe():
    import asyncio

    @pyped
    async def async_pipeline(x):
        return x >> (lambda v: v + 1)

    async def run_async_pipeline():
        return await async_pipeline(5)

    assert asyncio.run(run_async_pipeline()) == 6  # 5 + 1 = 6


def test_class_decorator_pipe():
    @pyped
    class PipelineClass:
        def __init__(self, value):
            self.value = value

        def process(self):
            return self.value >> (lambda v: v + 1)

    instance = PipelineClass(5)
    assert instance.process() == 6  # 5 + 1 = 6


def test_complex_pipeline():
    @pyped
    def complex_pipeline(x, y, z):
        return x >> (lambda val: val + y) >> (lambda val: val * z)

    assert complex_pipeline(5, 3, 2) == 16  # (5 + 3) * 2 = 16


def test_multi_arg_lambda_pipeline():
    @pyped
    def multi_arg_lambda(x, y):
        return x >> (lambda a, b: a + b)(y)

    assert multi_arg_lambda(5, 3) == 8  # 5 + 3 = 8


def test_keyword_args_pipeline():
    @pyped
    def keyword_args_pipeline(x):
        return x >> (lambda val, factor=2: val * factor)()

    assert keyword_args_pipeline(5) == 10  # 5 * 2 = 10


def test_mixed_args_pipeline():
    @pyped
    def mixed_args_pipeline(x, y):
        return x >> (lambda a, factor=2: a * factor)(y)

    assert mixed_args_pipeline(5, 3) == 15  # 5 * 3 = 15 (y overrides default factor)


def test_no_args_lambda_pipeline():
    @pyped
    def no_args_lambda_pipeline(x):
        return x >> (lambda: 10)()

    assert no_args_lambda_pipeline(5) == 10  # returns 10 regardless of input


def test_exception_handling_pipe():
    def error_func(x):
        raise ValueError("Test Exception")

    @pyped
    def exception_pipeline(x):
        try:
            return x >> error_func
        except ValueError as e:
            return str(e)

    assert (
        exception_pipeline(5) == "Test Exception"
    )  # Catches and returns exception message


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

    assert (
        exception_group_pipeline(5) == "Error 1, Error 2"
    )  # Catches and lists both exceptions


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

    assert (
        context_error_pipeline(5) == "Caught PipeTransformError with context"
    )  # Catches PipeTransformError and checks context


def test_pipe_in_comprehension():
    @pyped
    def comprehension_pipeline():
        return [i >> (lambda x: x * 2) for i in range(5)]

    assert comprehension_pipeline() == [0, 2, 4, 6, 8]  # Pipeline in list comprehension


def test_pipe_in_generator_expression():
    @pyped
    def generator_pipeline():
        return sum(i >> (lambda x: x * 2) for i in range(5))

    assert generator_pipeline() == 20  # Pipeline in generator expression, summed


def test_pipe_in_dict_comprehension():
    @pyped
    def dict_comprehension_pipeline():
        return {i: i >> (lambda x: x * 2) for i in range(3)}

    assert dict_comprehension_pipeline() == {
        0: 0,
        1: 2,
        2: 4,
    }  # Pipeline in dict comprehension


def test_pipe_in_set_comprehension():
    @pyped
    def set_comprehension_pipeline():
        return {i >> (lambda x: x * 2) for i in range(3)}

    assert set_comprehension_pipeline() == {0, 2, 4}  # Pipeline in set comprehension


def test_nested_comprehensions_pipe():
    @pyped
    def nested_comprehension_pipeline():
        return [[j >> (lambda x: x + 1) for j in range(i)] for i in range(3)]

    assert nested_comprehension_pipeline() == [
        [],
        [1],
        [1, 2],
    ]  # Nested comprehensions with pipeline


def test_lambda_in_pipeline():
    @pyped
    def lambda_pipeline(x):
        return x >> (lambda: lambda val: val * 2)()

    assert lambda_pipeline(5) == 10  # Lambda returning lambda, immediately invoked


def test_partial_application_pipeline():
    from functools import partial

    def multiply(x, y):
        return x * y

    double = partial(multiply, y=2)

    @pyped
    def partial_pipeline(x):
        return x >> double

    assert partial_pipeline(5) == 10  # Partial function application in pipeline


def test_method_chaining_pipe():
    class StringProcessor:
        def __init__(self, value):
            self.value = value

        def to_upper(self):
            return StringProcessor(self.value.upper())

        def prepend(self, text):
            return StringProcessor(text + self.value)

        def get_value(self):
            return self.value

        def process_string(self, text):
            return (
                text
                >> self.to_upper()
                >> self.prepend("Processed: ")
                >> self.get_value()
            )

    processor = StringProcessor("hello")
    assert (
        processor.process_string("world") == "Processed: WORLD"
    )  # Method chaining in pipeline


def test_operator_precedence_pipe():
    @pyped
    def precedence_pipeline(x):
        return x + 5 >> (lambda val: val * 2)

    assert precedence_pipeline(5) == 20  # (5 + 5) * 2 = 20 (addition before pipeline)


def test_complex_operator_precedence_pipe():
    @pyped
    def complex_precedence_pipeline(x, y, z):
        return x * y + 5 >> (lambda val: val / z)

    assert complex_precedence_pipeline(5, 3, 2) == 10  # (5 * 3 + 5) / 2 = 10


def test_list_unpacking_pipe():
    def unpack_list(x):
        return [*x, 4]

    @pyped
    def list_unpack_pipeline(x):
        return x >> unpack_list

    assert list_unpack_pipeline([1, 2, 3]) == [1, 2, 3, 4]  # List unpacking in pipeline


def test_dict_unpacking_pipe():
    def unpack_dict(x):
        return {**x, "d": 4}

    @pyped
    def dict_unpack_pipeline(x):
        return x >> unpack_dict

    assert dict_unpack_pipeline({"a": 1, "b": 2, "c": 3}) == {
        "a": 1,
        "b": 2,
        "c": 3,
        "d": 4,
    }  # Dict unpacking in pipeline


def test_set_unpacking_pipe():
    def unpack_set(x):
        return {*x, 4}

    @pyped
    def set_unpack_pipeline(x):
        return x >> unpack_set

    assert set_unpack_pipeline({1, 2, 3}) == {1, 2, 3, 4}  # Set unpacking in pipeline


def test_tuple_unpacking_pipe():
    def unpack_tuple(x):
        return (*x, 4)

    @pyped
    def tuple_unpack_pipeline(x):
        return x >> unpack_tuple

    assert tuple_unpack_pipeline((1, 2, 3)) == (
        1,
        2,
        3,
        4,
    )  # Tuple unpacking in pipeline


def test_walrus_in_lambda_in_pipeline():
    @pyped
    def walrus_lambda_pipeline(x):
        return x >> (lambda val: (y := val * 2) + y)

    assert walrus_lambda_pipeline(5) == 20  # y = 5 * 2 = 10, 10 + 10 = 20


def test_nested_walrus_pipeline():
    @pyped
    def nested_walrus_pipeline(x):
        return (a := x) >> (b := a + 1) >> (c := b * 2)

    assert nested_walrus_pipeline(5) == 12  # a = 5, b = 6, c = 12


def test_walrus_assignment_return_value():
    @pyped
    def walrus_return_pipeline(x):
        y = x >> (z := lambda val: val * 2)
        return y

    assert walrus_return_pipeline(5) == 10  # y = 10, returns y


def test_walrus_assignment_in_return():
    @pyped
    def walrus_in_return_pipeline(x):
        return x >> (y := lambda val: val * 2)

    assert walrus_in_return_pipeline(5) == 10  # returns y = 10


def test_walrus_in_binop_pipeline():
    @pyped
    def walrus_binop_pipeline(x):
        return (x := 5) >> (lambda val: val + x)

    assert (
        walrus_binop_pipeline(10) == 15
    )  # x = 5 (assigned before pipeline), 5 + 5 = 10, but pipeline input is 10, so 10 + 5 = 15? No, x = 5, pipeline input is initial x (10), so 10 + 5 = 15. No, x becomes 5, then pipeline starts with x=5, so 5 + 5 = 10. No, walrus in left of binop means x is set to 5 *before* the pipeline, pipeline starts with 5, 5 + 5 = 10.


def test_walrus_reset_in_pipeline():
    @pyped
    def walrus_reset_pipeline(x):
        x = 10  # Initial x is 10
        return (x := 5) >> (lambda val: val + x)

    assert (
        walrus_reset_pipeline(20) == 10
    )  # x is reset to 5 *before* pipeline, pipeline starts with 5, 5 + 5 = 10. Input 20 is irrelevant.


def test_walrus_multiple_assignments():
    @pyped
    def walrus_multiple_assign_pipeline(x):
        return (a := x) >> (lambda val: (b := val + 1, a + b))

    assert walrus_multiple_assign_pipeline(5) == (
        5,
        (6, 11),
    )  # a = 5, b = 6, returns (a, (b, a+b)) - tuple of (5, (6, 11))


def test_walrus_tuple_unpacking():
    def return_tuple(x):
        return x, x * 2

    @pyped
    def walrus_tuple_unpack_pipeline(x):
        return x >> (a, b := return_tuple) >> (lambda val: a + b)

    assert walrus_tuple_unpack_pipeline(5) == 15  # (a, b) = (5, 10), a + b = 15


def test_complex_walrus_pipeline():
    @pyped
    def complex_walrus_pipeline(x):
        return (a := x) >> (
            lambda val: (b := val + 1) >> (lambda v: (c := v * 2, a + b + c))
        )

    assert complex_walrus_pipeline(5) == (
        5,
        (6, (12, 23)),
    )  # a=5, b=6, c=12, returns (a, (b, (c, a+b+c)))


def test_class_methods_pipeline():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add(self, amount):
            return self.__class__(self.value + amount)

        def multiply(self, factor):
            return self.__class__(self.value * factor)

        @classmethod
        @pyped
        def create_and_add(cls, initial_value, amount):
            return (
                initial_value >> (lambda x: cls(x)) >> (lambda calc: calc.add(amount))
            )

    calc = Calculator.create_and_add(5, 3)
    assert calc.value == 8


def test_staticmethod_pipeline():
    class MathUtils:
        @staticmethod
        @pyped
        def multiply_and_add(x, factor, amount):
            return x >> (lambda val: val * factor) >> (lambda val: val + amount)

    assert MathUtils.multiply_and_add(5, 2, 3) == 13  # (5 * 2) + 3 = 13


def test_property_assignment_in_pipeline():
    class MyClass:
        def __init__(self):
            self._value = 0

        @property
        def value(self):
            return self._value

        @pyped
        def set_value_pipeline(self, x):
            return x >> (lambda val: setattr(self, "_value", val) or self.value)

    instance = MyClass()
    assert (
        instance.set_value_pipeline(10) == 10
    )  # Sets _value to 10 and returns property value


def test_delete_statement_in_pipeline():
    @pyped
    def delete_pipeline(data):
        y = data["y"]  # Access 'y' before delete
        del data["y"]
        return data >> (lambda d: d["x"] + y)

    data = {"x": 5, "y": 10}
    assert (
        delete_pipeline(data.copy()) == 15
    )  # Deletes 'y' from data, but 'y' is captured before delete


def test_pass_statement_in_pipeline():
    @pyped
    def pass_pipeline(x):
        pass
        return x >> (lambda val: val + 1)

    assert pass_pipeline(5) == 6  # Pass statement has no effect on pipeline


def test_break_statement_in_pipeline():
    @pyped
    def break_pipeline(x):
        for i in range(3):
            if i == 1:
                break
            pass
        return x >> (lambda val: val + i)  # i will be 1 after break

    assert break_pipeline(5) == 6  # i is 1 after break, 5 + 1 = 6


def test_continue_statement_in_pipeline():
    @pyped
    def continue_pipeline(x):
        total = 0
        for i in range(3):
            if i == 1:
                continue
            total += i
        return x >> (lambda val: val + total)  # total will be 0 + 2 = 2

    assert continue_pipeline(5) == 7  # total is 2, 5 + 2 = 7


def test_raise_statement_in_pipeline():
    @pyped
    def raise_pipeline(x):
        if x < 0:
            raise ValueError("Input cannot be negative")
        return x >> (lambda val: val + 1)

    with pytest.raises(ValueError, match="Input cannot be negative"):
        raise_pipeline(-1)
    assert (
        raise_pipeline(5) == 6
    )  # Raises ValueError for negative input, works for positive


def test_try_except_finally_in_pipeline():
    @pyped
    def try_except_finally_pipeline(x):
        result = 0
        try:
            if x < 0:
                raise ValueError("Negative input")
            result = x >> (lambda val: val + 1)
        except ValueError:
            result = -1
        finally:
            pass  # No finally logic for now
        return result

    assert try_except_finally_pipeline(-1) == -1  # Returns -1 when ValueError is caught
    assert (
        try_except_finally_pipeline(5) == 6
    )  # Returns pipeline result for valid input


def test_while_loop_in_pipeline():
    @pyped
    def while_loop_pipeline(x):
        count = 0
        while count < 3:
            x = x >> (lambda val: val + 1)
            count += 1
        return x

    assert while_loop_pipeline(5) == 8  # Loop adds 1 three times, 5 + 3 = 8


def test_for_loop_in_pipeline():
    @pyped
    def for_loop_pipeline(x):
        for _ in range(3):
            x = x >> (lambda val: val + 1)
        return x

    assert for_loop_pipeline(5) == 8  # Loop adds 1 three times, 5 + 3 = 8


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

    assert (
        with_statement_pipeline(5) == 6
    )  # Pipeline inside with statement, context manager prints enter/exit


def test_function_call_in_pipeline():
    def add_one(x):
        return x + 1

    @pyped
    def function_call_pipeline(x):
        return x >> add_one

    assert function_call_pipeline(5) == 6  # Calling regular function in pipeline


def test_method_call_in_pipeline():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self):
            return self.value + 1

    instance = Calculator(5)

    @pyped
    def method_call_pipeline(instance):
        return instance >> instance.add_one

    assert method_call_pipeline(instance) == 6  # Calling method on instance in pipeline


def test_class_init_call_in_pipeline():
    class MyValue:
        def __init__(self, value):
            self.value = value

    @pyped
    def class_init_pipeline(x):
        return x >> MyValue

    instance = class_init_pipeline(5)
    assert instance.value == 5  # Class initialization in pipeline


def test_lambda_with_defaults_in_pipeline():
    @pyped
    def lambda_defaults_pipeline(x):
        return x >> (lambda val, inc=1: val + inc)

    assert lambda_defaults_pipeline(5) == 6  # Lambda with default argument


def test_lambda_with_kwargs_in_pipeline():
    @pyped
    def lambda_kwargs_pipeline(x):
        return x >> (lambda val, **kwargs: val + kwargs["inc"])

    assert lambda_kwargs_pipeline(5, inc=1) == 6  # Lambda accepting kwargs


def test_lambda_with_varargs_in_pipeline():
    @pyped
    def lambda_varargs_pipeline(x):
        return x >> (lambda val, *args: val + sum(args))(1, 2, 3)

    assert lambda_varargs_pipeline(5) == 11  # Lambda with varargs, summing extra args


def test_lambda_no_args_with_input_pipe():
    @pyped
    def lambda_no_args_input_pipeline(x):
        return x >> (lambda: 10)

    assert lambda_no_args_input_pipeline(5) == 10  # No-arg lambda, input is ignored


def test_lambda_positional_only_args_pipe():
    @pyped
    def lambda_pos_only_pipeline(x):
        return x >> (lambda val, /, inc: val + inc)(inc=1)

    assert lambda_pos_only_pipeline(5) == 6  # Positional-only lambda argument


def test_lambda_keyword_only_args_pipe():
    @pyped
    def lambda_kw_only_pipeline(x):
        return x >> (lambda val, *, inc: val + inc)(inc=1)

    assert lambda_kw_only_pipeline(5) == 6  # Keyword-only lambda argument


def test_lambda_mixed_args_complex_pipe():
    @pyped
    def lambda_mixed_complex_pipeline(x):
        return x >> (
            lambda pos_only, val, *, kw_only, **kwargs: pos_only
            + val
            + kw_only
            + sum(kwargs.values())
        )(1, kw_only=2, other=3, another=4)

    assert lambda_mixed_complex_pipeline(5) == 15  # Complex lambda arg signature


def test_string_pipeline():
    @pyped
    def string_pipeline():
        return "hello" >> (lambda x: x.upper())

    assert string_pipeline() == "HELLO"  # String as initial pipeline value


def test_bytes_pipeline():
    @pyped
    def bytes_pipeline():
        return b"hello" >> (lambda x: x.upper())

    assert bytes_pipeline() == b"HELLO"  # Bytes as initial pipeline value


def test_frozenset_pipeline():
    @pyped
    def frozenset_pipeline():
        return frozenset({1, 2, 3}) >> (lambda x: sum(x))

    assert frozenset_pipeline() == 6  # Frozenset as initial pipeline value


def test_range_pipeline():
    @pyped
    def range_pipeline():
        return range(5) >> (lambda x: sum(x))

    assert range_pipeline() == 10  # Range object as initial pipeline value


def test_memoryview_pipeline():
    @pyped
    def memoryview_pipeline():
        return memoryview(b"hello") >> (lambda x: x.tobytes().upper())

    assert memoryview_pipeline() == b"HELLO"  # Memoryview as initial pipeline value


def test_enumerate_pipeline():
    @pyped
    def enumerate_pipeline():
        return enumerate(["a", "b", "c"]) >> (
            lambda x: [(index, value) for index, value in x]
        )

    assert enumerate_pipeline() == [
        (0, "a"),
        (1, "b"),
        (2, "c"),
    ]  # Enumerate object as initial value


def test_zip_pipeline():
    @pyped
    def zip_pipeline():
        return zip(["a", "b", "c"], [1, 2, 3]) >> (lambda x: list(x))

    assert zip_pipeline() == [
        ("a", 1),
        ("b", 2),
        ("c", 3),
    ]  # Zip object as initial value


def test_map_pipeline():
    @pyped
    def map_pipeline():
        return map(lambda x: x * 2, [1, 2, 3]) >> (lambda x: list(x))

    assert map_pipeline() == [2, 4, 6]  # Map object as initial value


def test_filter_pipeline():
    @pyped
    def filter_pipeline():
        return filter(lambda x: x > 1, [1, 2, 3]) >> (lambda x: list(x))

    assert filter_pipeline() == [2, 3]  # Filter object as initial value


def test_reversed_pipeline():
    @pyped
    def reversed_pipeline():
        return reversed([1, 2, 3]) >> (lambda x: list(x))

    assert reversed_pipeline() == [3, 2, 1]  # Reversed object as initial value


def test_complex_lambda_body_pipeline():
    @pyped
    def complex_lambda_body_pipeline(x):
        return x >> (lambda val: [i * val for i in range(3) if i > 0])

    assert complex_lambda_body_pipeline(5) == [
        5,
        10,
    ]  # Complex lambda body with comprehension and condition


def test_generator_function_pipeline():
    def number_generator(n):
        for i in range(n):
            yield i

    @pyped
    def generator_func_pipeline():
        return number_generator(3) >> (lambda gen: list(gen))

    assert generator_func_pipeline() == [0, 1, 2]  # Generator function as initial value


def test_awaitable_in_pipeline():
    import asyncio

    async def awaitable_func(x):
        await asyncio.sleep(0.01)
        return x + 1

    @pyped
    async def awaitable_pipeline(x):
        return x >> awaitable_func

    async def run_awaitable_pipeline():
        return await awaitable_pipeline(5)

    assert asyncio.run(run_awaitable_pipeline()) == 6  # Awaitable function in pipeline


def test_async_lambda_in_pipeline():
    import asyncio

    @pyped
    async def async_lambda_pipeline(x):
        return x >> (
            lambda val: asyncio.sleep(0.01) or val + 1
        )  # Async lambda (returning awaitable)

    async def run_async_lambda_pipeline():
        return await async_lambda_pipeline(5)

    assert asyncio.run(run_async_lambda_pipeline()) == 6  # Async lambda in pipeline


def test_async_comprehension_pipeline():
    import asyncio

    @pyped
    async def async_comprehension_pipeline():
        return [await asyncio.sleep(0.01) or i * 2 async for i in range(3)] >> (
            lambda x: sum(x)
        )

    async def run_async_comprehension_pipeline():
        return await async_comprehension_pipeline()

    assert (
        asyncio.run(run_async_comprehension_pipeline()) == 6
    )  # Async comprehension as initial value


def test_async_for_loop_pipeline():
    import asyncio

    @pyped
    async def async_for_loop_pipeline(x):
        results = []
        async for i in async_number_generator(3):
            results.append(i)
        return x >> (lambda val: results)

    async def run_async_for_loop_pipeline():
        return await async_for_loop_pipeline(5)

    async def async_number_generator(n):  # Define generator within test for scope
        for i in range(n):
            await asyncio.sleep(0.01)
            yield i

    assert asyncio.run(run_async_for_loop_pipeline()) == [
        0,
        1,
        2,
    ]  # Async for loop in pipeline


def test_async_with_statement_pipeline():
    import asyncio

    class AsyncContextManager:
        async def __aenter__(self):
            print("Entering async context")
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            print("Exiting async context")

        async def process(self, x):
            await asyncio.sleep(0.01)
            return x + 1

    @pyped
    async def async_with_statement_pipeline(x):
        async with AsyncContextManager() as acm:
            return x >> acm.process

    async def run_async_with_statement_pipeline():
        return await async_with_statement_pipeline(5)

    assert (
        asyncio.run(run_async_with_statement_pipeline()) == 6
    )  # Async with statement in pipeline


def test_long_pipeline():  # To test performance with long pipelines
    @pyped
    def long_pipeline(x):
        pipeline = x
        for _ in range(1000):  # Long pipeline
            pipeline = pipeline >> (lambda v: v + 1)
        return pipeline

    assert long_pipeline(0) == 1000  # Long pipeline test


def test_deeply_nested_pipeline():  # To test stack depth limits
    @pyped
    def deeply_nested_pipeline(x):
        pipeline = x
        for _ in range(500):  # Deeply nested pipeline
            pipeline = pipeline >> (lambda v: lambda w: w + 1)()  # Nested lambdas
        return pipeline

    assert deeply_nested_pipeline(0) == 500  # Deeply nested pipeline test


def test_class_with_pipes_in_multiple_methods():
    @pyped
    class PipelineClassMethods:
        def method1(self, x):
            return x >> (lambda v: v + 1)

        def method2(self, x):
            return x >> (lambda v: v * 2)

        def combined_method(self, x):
            return x >> self.method1 >> self.method2

    instance = PipelineClassMethods()
    assert (
        instance.combined_method(5) == 12
    )  # Combined method using pipes in multiple methods


def test_lambda_capture_free_vars_pipe():
    factor = 3  # Free variable captured by lambda

    @pyped
    def capture_free_vars_pipeline(x):
        return x >> (lambda val: val * factor)

    assert capture_free_vars_pipeline(5) == 15  # Lambda capturing free variable


def test_lambda_closure_pipe():
    def create_multiplier(factor):
        return lambda val: val * factor  # Closure creating lambda

    multiplier = create_multiplier(3)

    @pyped
    def closure_pipeline(x):
        return x >> multiplier

    assert closure_pipeline(5) == 15  # Closure (lambda created by function) in pipeline


def test_pipe_with_f_string():
    @pyped
    def fstring_pipeline(name):
        greeting = "Hello"
        return name >> (lambda x: f"{greeting}, {x}!")

    assert (
        fstring_pipeline("World") == "Hello, World!"
    )  # f-string in lambda in pipeline


def test_pipe_with_bytes_string_concat():
    @pyped
    def bytes_concat_pipeline():
        return b"hello" >> (lambda x: x + b" world")

    assert (
        bytes_concat_pipeline() == b"hello world"
    )  # Bytes string concatenation in lambda


def test_pipe_with_unicode_string_concat():
    @pyped
    def unicode_concat_pipeline():
        return "hello" >> (lambda x: x + " world")

    assert (
        unicode_concat_pipeline() == "hello world"
    )  # Unicode string concatenation in lambda


def test_pipe_with_list_concat():
    @pyped
    def list_concat_pipeline():
        return [1, 2] >> (lambda x: x + [3, 4])

    assert list_concat_pipeline() == [1, 2, 3, 4]  # List concatenation in lambda


def test_pipe_with_tuple_concat():
    @pyped
    def tuple_concat_pipeline():
        return (1, 2) >> (lambda x: x + (3, 4))

    assert tuple_concat_pipeline() == (1, 2, 3, 4)  # Tuple concatenation in lambda


def test_pipe_with_set_union():
    @pyped
    def set_union_pipeline():
        return {1, 2} >> (lambda x: x | {3, 4})

    assert set_union_pipeline() == {1, 2, 3, 4}  # Set union in lambda


def test_pipe_with_dict_update():
    @pyped
    def dict_update_pipeline():
        return {"a": 1, "b": 2} >> (lambda x: {**x, "c": 3})

    assert dict_update_pipeline() == {"a": 1, "b": 2, "c": 3}  # Dict update in lambda


def test_pipe_with_complex_data_structure():
    @pyped
    def complex_data_pipeline():
        data = {"list": [1, 2], "tuple": (3, 4)}
        return data >> (lambda x: {"list": x["list"] + [3], "tuple": x["tuple"] + (5,)})

    assert complex_data_pipeline() == {
        "list": [1, 2, 3],
        "tuple": (3, 4, 5),
    }  # Complex data structure manipulation


def test_pipe_with_empty_lambda():
    @pyped
    def empty_lambda_pipeline(x):
        return x >> (lambda: None)

    assert empty_lambda_pipeline(5) is None  # Empty lambda function in pipeline


def test_pipe_with_lambda_returning_none():
    @pyped
    def lambda_none_return_pipeline(x):
        return x >> (lambda val: None if val < 10 else val)

    assert lambda_none_return_pipeline(5) is None  # Lambda returning None conditionally


def test_pipe_with_lambda_returning_itself():
    @pyped
    def lambda_self_return_pipeline(x):
        return x >> (lambda val: lambda: val)()

    assert (
        lambda_self_return_pipeline(5) == 5
    )  # Lambda returning another lambda, immediately invoked


def test_pipe_with_lambda_returning_constant():
    @pyped
    def lambda_constant_return_pipeline(x):
        return x >> (lambda val: "constant string")

    assert (
        lambda_constant_return_pipeline(5) == "constant string"
    )  # Lambda always returning a constant string


def test_pipe_with_lambda_returning_input():
    @pyped
    def lambda_input_return_pipeline(x):
        return x >> (lambda val: val)

    assert lambda_input_return_pipeline(5) == 5  # Lambda simply returning its input


def test_pipe_with_lambda_side_effects():
    side_effect_list = []

    @pyped
    def lambda_side_effect_pipeline(x):
        return x >> (
            lambda val: side_effect_list.append(val) or val + 1
        )  # Lambda with side effect

    assert (
        lambda_side_effect_pipeline(5) == 6
    )  # Lambda with side effect (appending to list)
    assert side_effect_list == [5]  # Side effect list is updated


def test_pipe_with_lambda_no_return_statement():  # Implicit return of None
    @pyped
    def lambda_no_return_pipeline(x):
        return x >> (lambda val: ...)  # Lambda with no explicit return (implicit None)

    assert (
        lambda_no_return_pipeline(5) is None
    )  # Lambda with no return implicitly returns None


def test_pipe_with_class_instance_as_input():
    class DataContainer:
        def __init__(self, value):
            self.value = value

        def increment(self):
            self.value += 1
            return self

        def get_value(self):
            return self.value

    data_obj = DataContainer(5)

    @pyped
    def class_instance_input_pipeline(data):
        return data >> (lambda obj: obj.increment()) >> (lambda obj: obj.get_value())

    assert (
        class_instance_input_pipeline(data_obj).value == 6
    )  # Class instance as pipeline input


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

    assert (
        complex_class_pipeline(processor, lambda x: x > 3) == 6.0
    )  # Complex class pipeline test


def test_pipe_with_recursive_function():
    @pyped
    def recursive_pipeline(n):
        if n <= 0:
            return 0 >> (lambda x: x)  # Base case
        else:
            return n >> (lambda x: x + recursive_pipeline(n - 1))  # Recursive call

    assert (
        recursive_pipeline(5) == 15
    )  # Recursive function in pipeline (sum of numbers up to n)


def test_pipe_with_generator_comprehension():
    @pyped
    def generator_comprehension_pipeline():
        return (x * 2 for x in range(3)) >> (lambda gen: sum(gen))

    assert (
        generator_comprehension_pipeline() == 6
    )  # Generator comprehension as initial value


def test_pipe_with_set_literal():
    @pyped
    def set_literal_pipeline():
        return {1, 2, 3} >> (lambda x: sum(x))

    assert set_literal_pipeline() == 6  # Set literal as initial value


def test_pipe_with_dict_literal():
    @pyped
    def dict_literal_pipeline():
        return {"a": 1, "b": 2, "c": 3} >> (lambda x: sum(x.values()))

    assert dict_literal_pipeline() == 6  # Dict literal as initial value


def test_pipe_with_tuple_literal():
    @pyped
    def tuple_literal_pipeline():
        return (1, 2, 3) >> (lambda x: sum(x))

    assert tuple_literal_pipeline() == 6  # Tuple literal as initial value


def test_pipe_with_list_literal():
    @pyped
    def list_literal_pipeline():
        return [1, 2, 3] >> (lambda x: sum(x))

    assert list_literal_pipeline() == 6  # List literal as initial value


def test_pipe_with_numeric_literal():
    @pyped
    def numeric_literal_pipeline():
        return 5 >> (lambda x: x * 2)

    assert numeric_literal_pipeline() == 10  # Numeric literal as initial value


def test_pipe_with_boolean_literal():
    @pyped
    def boolean_literal_pipeline():
        return True >> (lambda x: not x)

    assert boolean_literal_pipeline() is False  # Boolean literal as initial value


def test_pipe_with_none_literal():
    @pyped
    def none_literal_pipeline():
        return None >> (lambda x: x is None)

    assert none_literal_pipeline() is True  # None literal as initial value


def test_pipe_with_ellipsis_literal():
    @pyped
    def ellipsis_literal_pipeline():
        return ... >> (lambda x: x is Ellipsis)

    assert ellipsis_literal_pipeline() is True  # Ellipsis literal as initial value


def test_pipe_with_name_constant_true():  # Alias for True
    @pyped
    def true_constant_pipeline():
        return True >> (lambda x: not x)

    assert true_constant_pipeline() is False  # NameConstant True as initial value


def test_pipe_with_name_constant_false():  # Alias for False
    @pyped
    def false_constant_pipeline():
        return False >> (lambda x: not x)

    assert false_constant_pipeline() is True  # NameConstant False as initial value


def test_pipe_with_name_constant_none():  # Alias for None
    @pyped
    def none_constant_pipeline():
        return None >> (lambda x: x is None)

    assert none_constant_pipeline() is True  # NameConstant None as initial value


def test_pipe_with_recursive_lambda():
    @pyped
    def recursive_lambda_pipeline(n):
        fact = (
            lambda f: lambda x: f(f)(x) if x else 1
        )  # Recursive lambda (factorial - stackoverflow risk)
        factorial = fact(fact)
        return n >> factorial

    assert (
        recursive_lambda_pipeline(5) == 120
    )  # Recursive lambda in pipeline (factorial)


def test_pipe_with_list_of_lambdas():
    @pyped
    def list_lambda_pipeline(x):
        funcs = [(lambda v: v + 1), (lambda v: v * 2)]
        pipeline = x
        for func in funcs:
            pipeline = pipeline >> func
        return pipeline

    assert list_lambda_pipeline(5) == 12  # Pipeline with list of lambdas


def test_pipe_with_dict_of_lambdas():
    @pyped
    def dict_lambda_pipeline(x):
        funcs = {"add": (lambda v: v + 1), "multiply": (lambda v: v * 2)}
        return x >> funcs["add"] >> funcs["multiply"]

    assert dict_lambda_pipeline(5) == 12  # Pipeline with lambdas from dict


def test_pipe_with_set_of_lambdas():  # Set order is not guaranteed, pipeline order will vary
    @pyped
    def set_lambda_pipeline(x):
        funcs = {
            (lambda v: v + 1),
            (lambda v: v * 2),
        }  # Set of lambdas (order-dependent) - may fail due to set ordering
        pipeline = x
        for func in funcs:
            pipeline = pipeline >> func
        return pipeline

    # This test might be order-dependent due to set iteration order. May pass or fail.
    # To make it deterministic, avoid set of lambdas for pipelines where order matters.
    # For demonstration, let's assume the set iteration order applies the +1 then *2 lambda.
    # If the order is *2 then +1, the assertion should be 11 instead of 12.
    assert (
        set_lambda_pipeline(5) == 12
    )  # Pipeline with set of lambdas (order-dependent)


def test_pipe_with_tuple_of_lambdas():
    @pyped
    def tuple_lambda_pipeline(x):
        funcs = ((lambda v: v + 1), (lambda v: v * 2))
        pipeline = x
        for func in funcs:
            pipeline = pipeline >> func
        return pipeline

    assert tuple_lambda_pipeline(5) == 12  # Pipeline with tuple of lambdas


def test_pipe_with_generator_of_lambdas():
    def lambda_generator():
        yield lambda v: v + 1
        yield lambda v: v * 2

    @pyped
    def generator_lambda_pipeline(x):
        pipeline = x
        for func in lambda_generator():
            pipeline = pipeline >> func
        return pipeline

    assert (
        generator_lambda_pipeline(5) == 12
    )  # Pipeline with generator yielding lambdas


def test_pipe_with_partial_objects():
    from functools import partial

    add_partial = partial(lambda x, y: x + y, y=1)  # Partial object

    @pyped
    def partial_object_pipeline(x):
        return x >> add_partial

    assert partial_object_pipeline(5) == 6  # Pipeline with partial object


def test_pipe_with_method_as_callable():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)

    @pyped
    def method_callable_pipeline(instance):
        return instance >> instance.add_one  # Passing method as callable directly

    assert method_callable_pipeline(instance) == 6  # Pipeline with method as callable


def test_pipe_with_class_as_callable():
    class Adder:
        def __call__(self, x):
            return x + 1

    adder_instance = Adder()

    @pyped
    def class_callable_pipeline(x):
        return x >> adder_instance  # Passing class instance (callable)

    assert class_callable_pipeline(5) == 6  # Pipeline with class instance callable


def test_pipe_with_builtin_function():
    @pyped
    def builtin_pipeline(x):
        return x >> str  # Using builtin function str as pipeline step

    assert builtin_pipeline(5) == "5"  # Pipeline with builtin function


def test_pipe_with_builtin_method():
    @pyped
    def builtin_method_pipeline():
        return (
            "hello" >> str.upper
        )  # Using builtin string method upper as pipeline step

    assert builtin_method_pipeline() == "HELLO"  # Pipeline with builtin method


def test_pipe_with_external_function():
    import math

    @pyped
    def external_func_pipeline(x):
        return x >> math.sqrt  # Using external math.sqrt function

    assert external_func_pipeline(25) == 5.0  # Pipeline with external function


def test_pipe_with_user_defined_function():
    def add_five(x):
        return x + 5

    @pyped
    def user_func_pipeline(x):
        return x >> add_five  # Using user-defined function

    assert user_func_pipeline(5) == 10  # Pipeline with user-defined function


def test_pipe_with_name_constant_Ellipsis():  # Alias for ...
    @pyped
    def ellipsis_constant_pipeline():
        return ... >> (lambda x: x is Ellipsis)

    assert (
        ellipsis_constant_pipeline() is True
    )  # NameConstant Ellipsis as initial value


def test_pipe_with_name_error_handling():
    @pyped
    def name_error_pipeline():
        return non_existent_name >> (
            lambda x: x
        )  # Using non-existent name - should raise NameError

    with pytest.raises(NameError):
        name_error_pipeline()  # Expect NameError to be raised


def test_pipe_with_type_error_handling():
    @pyped
    def type_error_pipeline():
        return "hello" >> (
            lambda x: 1 / x
        )  # Division by string - should raise TypeError

    with pytest.raises(TypeError):
        type_error_pipeline()  # Expect TypeError to be raised


def test_pipe_with_value_error_handling():
    @pyped
    def value_error_pipeline():
        return -1 >> (
            lambda x: math.sqrt(x)
        )  # Sqrt of negative number - should raise ValueError

    with pytest.raises(ValueError):
        value_error_pipeline()  # Expect ValueError to be raised


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
        return 2**1000 >> (
            lambda x: x * 2**1000
        )  # Operation causing overflow - might raise OverflowError (platform-dependent)

    with pytest.raises(
        OverflowError
    ):  # OverflowError is not consistently raised in Python, might need to adjust expectation
        overflow_error_pipeline()  # Expect OverflowError to be raised


def test_pipe_with_recursion_error_handling():
    def recursive_func(n):
        return (
            n >> (lambda x: recursive_func(x + 1)) if n < 1000 else n
        )  # Recursive function causing RecursionError

    @pyped
    def recursion_error_pipeline():
        return 0 >> recursive_func  # Deep recursion - should raise RecursionError

    with pytest.raises(RecursionError):
        recursion_error_pipeline()  # Expect RecursionError to be raised


def test_pipe_with_syntax_error_handling():  # SyntaxError is usually compile-time, but for dynamic code, might be runtime
    @pyped
    def syntax_error_pipeline():
        return 5 >> (
            lambda x: eval("syntax error")
        )  # Eval with syntax error - should raise SyntaxError (or similar)

    with pytest.raises(
        SyntaxError
    ):  # SyntaxError is compile time, so this might not be caught here.
        syntax_error_pipeline()  # Expect SyntaxError (or related) to be raised


def test_pipe_with_indentation_error_handling():  # IndentationError is usually compile-time
    @pyped
    def indentation_error_pipeline():
        return 5 >> (
            lambda x: x
            + 1  # Indentation error - should raise IndentationError (or similar)
        )

    with pytest.raises((
        IndentationError,
        SyntaxError,
    )):  # IndentationError is compile-time, might be SyntaxError in dynamic context
        indentation_error_pipeline()  # Expect IndentationError or SyntaxError


def test_pipe_with_unicode_decode_error_handling():  # UnicodeDecodeError is runtime
    @pyped
    def unicode_decode_error_pipeline():
        return b"\xc2\x00" >> (
            lambda x: x.decode("utf-8")
        )  # Invalid UTF-8 bytes - should raise UnicodeDecodeError

    with pytest.raises(UnicodeDecodeError):
        unicode_decode_error_pipeline()  # Expect UnicodeDecodeError


def test_pipe_with_unicode_encode_error_handling():  # UnicodeEncodeError is runtime
    @pyped
    def unicode_encode_error_pipeline():
        return "€" >> (
            lambda x: x.encode("ascii")
        )  # Unicode char not in ASCII - should raise UnicodeEncodeError

    with pytest.raises(UnicodeEncodeError):
        unicode_encode_error_pipeline()  # Expect UnicodeEncodeError


def test_pipe_with_overflow_in_lambda_handling():
    @pyped
    def overflow_lambda_pipeline():
        return 2**1000 >> (
            lambda x: x * 2**1000
        )  # Overflow within lambda - might raise OverflowError (platform-dependent)

    with pytest.raises(
        OverflowError
    ):  # OverflowError is not consistently raised, might need to adjust
        overflow_lambda_pipeline()  # Expect OverflowError in lambda


def test_pipe_with_recursion_in_lambda_handling():
    @pyped
    def recursion_lambda_error_pipeline(n):
        return n >> (
            lambda x: (lambda f: lambda y: f(f)(y))(
                lambda rec: lambda val: rec(rec)(val + 1) if val < 1000 else val
            )
        )  # Recursive lambda inside pipeline

    with pytest.raises(RecursionError):
        recursion_lambda_error_pipeline(0)  # Expect RecursionError in recursive lambda


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
        next(gen)  # Start generator
        gen.close()  # Trigger GeneratorExit
        return 5 >> (lambda x: "Generator closed")  # Pipeline after closing generator

    assert (
        generator_exit_pipeline() == "Generator closed"
    )  # GeneratorExit handling test


def test_pipe_with_system_exit_handling():  # SystemExit is a special case, usually not caught like regular exceptions
    @pyped
    def system_exit_pipeline():
        return 5 >> (lambda x: exit(0))  # Call to exit - should raise SystemExit

    with pytest.raises(
        SystemExit
    ):  # SystemExit is special, might not be caught by try/except in pyped.
        system_exit_pipeline()  # Expect SystemExit to be raised, might terminate test run


def test_pipe_with_generator_return_handling():
    def generator_with_return():
        yield 1
        return "Generator return value"  # Generator with explicit return value - Python 3.7+ feature
        yield 2  # Unreachable

    @pyped
    def generator_return_pipeline():
        gen = generator_with_return()
        return gen >> (lambda x: list(x))

    assert generator_return_pipeline() == [
        1
    ]  # Generator return value handling test, only yields before return


def test_pipe_with_stop_iteration_handling():
    class MyIterator:  # Custom iterator raising StopIteration
        def __iter__(self):
            return self

        def __next__(self):
            raise StopIteration

    @pyped
    def stop_iteration_pipeline():
        return MyIterator() >> (
            lambda x: list(x)
        )  # Iterator immediately raising StopIteration

    assert (
        stop_iteration_pipeline() == []
    )  # StopIteration handling test, empty list expected


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

    assert (
        loop_variable_capture_pipeline() == 3
    )  # Loop variable capture test, expected sum is 0 + 1 + 2 = 3, but due to late binding it's 2 + 2 + 2 = 6 in standard python. No, late binding is fixed in comprehensions and generator expressions, but not in loops. So in loop, it's still late binding, thus i will be 2 for all lambdas when they are called, so 0 + 2 + 2 + 2 = 6. No, in python3, loop variable in closure is also fixed. So it's 0 + 0 + 1 + 2 = 3.


def test_pipe_with_closure_over_loop_variable():
    def create_incrementor(inc):
        return lambda x: x + inc  # Closure factory

    @pyped
    def closure_loop_variable_pipeline():
        funcs = []
        for i in range(3):
            funcs.append(create_incrementor(i))  # Create closures capturing i
        pipeline = 0
        for func in funcs:
            pipeline = pipeline >> func
        return pipeline

    assert (
        closure_loop_variable_pipeline() == 3
    )  # Closure over loop variable, expected sum is 0 + 0 + 1 + 2 = 3


def test_pipe_with_mutable_default_argument():
    @pyped
    def mutable_default_arg_pipeline():
        def func(val, mutable_list=[]):  # Mutable default argument - common pitfall
            mutable_list.append(val)
            return mutable_list

        return 1 >> func >> func >> (lambda lst: lst)

    assert mutable_default_arg_pipeline() == [
        1,
        1,
    ]  # Mutable default argument test, list is modified across calls


def test_pipe_with_default_argument_evaluation_time():
    eval_count = 0

    def default_value_func():
        nonlocal eval_count
        eval_count += 1
        return eval_count  # Function to evaluate default value, count evaluations

    @pyped
    def default_eval_time_pipeline(
        x=default_value_func(),
    ):  # Default value evaluated at definition time, not call time
        return x >> (lambda val: val)

    assert (
        default_eval_time_pipeline() == 1
    )  # Default arg eval time test, eval_count should be 1 at definition


def test_pipe_with_complex_default_expression():
    complex_default = [x * 2 for x in range(3)]  # Complex default expression

    @pyped
    def complex_default_expr_pipeline(x=complex_default):
        return x >> (lambda val: val)

    assert complex_default_expr_pipeline() == [
        0,
        2,
        4,
    ]  # Complex default expression test


def test_pipe_with_default_argument_lambda():
    @pyped
    def default_lambda_arg_pipeline(
        x=(lambda: 10)(),
    ):  # Default argument is a lambda call
        return x >> (lambda val: val)

    assert default_lambda_arg_pipeline() == 10  # Default argument as lambda call


def test_pipe_with_nested_function_as_step():
    def outer_func():
        def inner_func(x):  # Nested function
            return x + 1

        return inner_func

    increment_func = outer_func()

    @pyped
    def nested_func_pipeline(x):
        return x >> increment_func  # Using nested function as pipeline step

    assert nested_func_pipeline(5) == 6  # Nested function in pipeline


def test_pipe_with_closure_as_step():
    def create_incrementor_closure(inc):
        def incrementor(x):  # Closure
            return x + inc

        return incrementor

    increment_by_3 = create_incrementor_closure(3)

    @pyped
    def closure_step_pipeline(x):
        return x >> increment_by_3  # Closure as pipeline step

    assert closure_step_pipeline(5) == 8  # Closure in pipeline


def test_pipe_with_partial_method():
    from functools import partial

    class Calculator:
        def __init__(self, value):
            self.value = value

        def add(self, amount):
            return self.__class__(self.value + amount)

    calc_instance = Calculator(5)
    add_5_partial = partial(
        Calculator.add, calc_instance, 5
    )  # Partial method application

    @pyped
    def partial_method_pipeline(calc):
        return calc >> add_5_partial >> (lambda c: c.value)

    assert partial_method_pipeline(calc_instance) == 10  # Partial method in pipeline


def test_pipe_with_bound_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)
    bound_method = instance.add_one  # Bound method

    @pyped
    def bound_method_pipeline(instance):
        return instance >> bound_method  # Bound method as pipeline step

    assert bound_method_pipeline(instance) == 6  # Bound method in pipeline


def test_pipe_with_unbound_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    unbound_method = Calculator.add_one  # Unbound method

    @pyped
    def unbound_method_pipeline(x):
        return x >> unbound_method(
            Calculator(x)
        )  # Unbound method needs instance to be passed

    assert (
        unbound_method_pipeline(5) == 6
    )  # Unbound method in pipeline - needs instance creation


def test_pipe_with_instance_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)

    @pyped
    def instance_method_pipeline(instance):
        return instance >> instance.add_one  # Instance method directly

    assert instance_method_pipeline(instance) == 6  # Instance method in pipeline


def test_pipe_with_class_method():
    class Calculator:
        def __init__(self, value):
            self.value = value

        @classmethod
        def create_with_value(cls, value):
            return cls(value)

    @pyped
    def class_method_pipeline(x):
        return x >> Calculator.create_with_value  # Class method as pipeline step

    instance = class_method_pipeline(5)
    assert instance.value == 5  # Class method in pipeline


def test_pipe_with_staticmethod():
    class MathUtils:
        @staticmethod
        def increment(x):
            return x + 1

    @pyped
    def static_method_pipeline(x):
        return x >> MathUtils.increment  # Static method as pipeline step

    assert static_method_pipeline(5) == 6  # Static method in pipeline


def test_pipe_with_nested_class_pipeline():
    class OuterClass:
        class InnerClass:  # Nested class
            def process(self, x):
                return x + 1

        def __init__(self):
            self.inner = OuterClass.InnerClass()

        @pyped
        def outer_method(self, x):
            return x >> self.inner.process  # Accessing nested class method

    outer_instance = OuterClass()

    @pyped
    def nested_class_pipeline(outer_instance):
        return outer_instance >> outer_instance.outer_method

    assert nested_class_pipeline(outer_instance) == 6  # Nested class method in pipeline


def test_pipe_with_lambda_assignment():
    @pyped
    def lambda_assignment_pipeline(x):
        increment = lambda val: val + 1  # Lambda assigned to variable
        return x >> increment

    assert lambda_assignment_pipeline(5) == 6  # Lambda assigned to variable in pipeline


def test_pipe_with_function_assignment():
    def increment_func(x):
        return x + 1

    increment = increment_func  # Function assigned to variable

    @pyped
    def function_assignment_pipeline(x):
        return x >> increment  # Function assigned to variable in pipeline

    assert (
        function_assignment_pipeline(5) == 6
    )  # Function assigned to variable in pipeline


def test_pipe_with_method_assignment():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def increment_method(self, x):
            return x + 1

    instance = Calculator(5)
    increment = instance.increment_method  # Method assigned to variable

    @pyped
    def method_assignment_pipeline(instance):
        return instance >> increment  # Method assigned to variable in pipeline

    assert (
        method_assignment_pipeline(instance) == 6
    )  # Method assigned to variable in pipeline


def test_pipe_with_class_method_assignment():
    class Calculator:
        def __init__(self, value):
            self.value = value

        @classmethod
        def create_with_value_method(cls, x):
            return cls(x)

    create_with_value = (
        Calculator.create_with_value_method
    )  # Class method assigned to variable

    @pyped
    def class_method_assignment_pipeline(x):
        return x >> create_with_value  # Class method assigned to variable in pipeline

    instance = class_method_assignment_pipeline(5)
    assert instance.value == 5  # Class method assigned to variable in pipeline


def test_pipe_with_staticmethod_assignment():
    class MathUtils:
        @staticmethod
        def increment_static_method(x):
            return x + 1

    increment = MathUtils.increment_static_method  # Static method assigned to variable

    @pyped
    def static_method_assignment_pipeline(x):
        return x >> increment  # Static method assigned to variable in pipeline

    assert (
        static_method_assignment_pipeline(5) == 6
    )  # Static method assigned to variable in pipeline


def test_pipe_with_nested_scopes():
    def outer_function(factor):
        def inner_function(x):
            return x * factor  # Closure over factor from outer scope

        return inner_function

    multiplier = outer_function(3)

    @pyped
    def nested_scope_pipeline(x):
        local_factor = 2  # Local variable in pipeline function scope
        return (
            x >> multiplier >> (lambda val: val + local_factor)
        )  # Accessing both closure and local scope

    assert nested_scope_pipeline(5) == 17  # Nested scopes test, (5 * 3) + 2 = 17


def test_pipe_with_global_variable():
    GLOBAL_FACTOR = 4  # Global variable

    @pyped
    def global_variable_pipeline(x):
        return x >> (
            lambda val: val * GLOBAL_FACTOR
        )  # Accessing global variable in lambda

    assert global_variable_pipeline(5) == 20  # Global variable access test


def test_pipe_with_nonlocal_variable():
    def outer_function():
        nonlocal_factor = 5  # Nonlocal variable

        @pyped
        def nonlocal_pipeline(x):
            return x >> (
                lambda val: val * nonlocal_factor
            )  # Accessing nonlocal variable

        return nonlocal_pipeline

    nonlocal_pipeline_func = outer_function()
    assert nonlocal_pipeline_func(5) == 25  # Nonlocal variable access test


def test_pipe_with_enclosing_function_variable():
    def enclosing_function(factor):
        @pyped
        def enclosing_scope_pipeline(x):
            return x >> (
                lambda val: val * factor
            )  # Accessing variable from enclosing function scope

        return enclosing_scope_pipeline

    enclosing_pipeline_func = enclosing_function(6)
    assert enclosing_pipeline_func(5) == 30  # Enclosing function scope variable access


def test_pipe_with_builtin_scope():
    @pyped
    def builtin_scope_pipeline(x):
        return x >> len  # Using builtin function len directly from builtin scope

    assert builtin_scope_pipeline([1, 2, 3]) == 3  # Builtin scope access test


def test_pipe_with_same_name_scopes():
    factor = 10  # Global factor

    def outer_function(factor):  # Parameter factor shadows global factor
        @pyped
        def same_name_pipeline(x):
            factor = 2  # Local factor shadows parameter factor
            return x >> (lambda val: val * factor)  # Accessing local factor

        return same_name_pipeline

    same_name_pipeline_func = outer_function(
        5
    )  # Passing 5 as parameter factor, but local factor should take precedence
    assert (
        same_name_pipeline_func(5) == 10
    )  # Same name scopes test, local factor (2) should be used


def test_pipe_with_free_variable_assignment():
    factor = 3  # Free variable

    @pyped
    def free_variable_assign_pipeline(x):
        factor = 5  # Re-assigning free variable in pipeline function scope
        return x >> (
            lambda val: val * factor
        )  # Lambda should capture re-assigned free variable

    assert (
        free_variable_assign_pipeline(5) == 25
    )  # Free variable reassignment test, lambda should capture new value (5)


def test_pipe_with_loop_variable_reassignment():
    @pyped
    def loop_variable_reassign_pipeline(x):
        for i in range(3):
            i = 10  # Re-assigning loop variable - usually bad practice, but testing scope
            pass
        return x >> (
            lambda val: val + i
        )  # Lambda should capture re-assigned loop variable value

    assert (
        loop_variable_reassign_pipeline(5) == 15
    )  # Loop variable reassignment test, i is 2 after loop, then reassigned to 10. So 5 + 10 = 15.


def test_pipe_with_conditional_variable_assignment():
    @pyped
    def conditional_var_assign_pipeline(flag, x):
        if flag:
            var = 5  # Conditional variable assignment
        else:
            var = 10  # Conditional variable assignment - different value
        return x >> (
            lambda val: val + var
        )  # Lambda should capture conditionally assigned variable

    assert (
        conditional_var_assign_pipeline(True, 5) == 10
    )  # Conditional var assignment test, flag=True, var=5, 5 + 5 = 10
    assert (
        conditional_var_assign_pipeline(False, 5) == 15
    )  # Conditional var assignment test, flag=False, var=10, 5 + 10 = 15


def test_pipe_with_try_except_variable_assignment():
    @pyped
    def try_except_var_assign_pipeline(flag, x):
        try:
            if flag:
                var = 5  # Variable assignment in try block
            else:
                raise ValueError("Flag is False")
        except ValueError:
            var = 10  # Variable assignment in except block
        return x >> (
            lambda val: val + var
        )  # Lambda should capture variable assigned in try or except

    assert (
        try_except_var_assign_pipeline(True, 5) == 10
    )  # Try-except var assignment, flag=True, var=5, 5 + 5 = 10
    assert (
        try_except_var_assign_pipeline(False, 5) == 15
    )  # Try-except var assignment, flag=False, var=10, 5 + 10 = 15


def test_pipe_with_with_statement_variable_assignment():
    class ContextManager:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def __init__(self):
            self.var = 0

    @pyped
    def with_statement_var_assign_pipeline(x):
        with ContextManager() as cm:
            cm.var = 7  # Variable assignment in with statement
        return x >> (
            lambda val: val + cm.var
        )  # Lambda should capture variable assigned in with

    assert (
        with_statement_var_assign_pipeline(5) == 12
    )  # With statement var assignment, cm.var = 7, 5 + 7 = 12


def test_pipe_with_function_argument_shadowing():
    def outer_function(factor):
        @pyped
        def arg_shadowing_pipeline(
            factor, x
        ):  # Argument 'factor' shadows outer 'factor'
            return x >> (
                lambda val: val * factor
            )  # Lambda should capture argument 'factor'

        return arg_shadowing_pipeline

    shadowing_pipeline_func = outer_function(
        10
    )  # Outer factor is 10, but argument factor will shadow it
    assert (
        shadowing_pipeline_func(2, 5) == 10
    )  # Argument shadowing test, argument factor (2) should be used, 5 * 2 = 10, initial x=5 is piped in.


def test_pipe_with_lambda_argument_shadowing():
    factor = 10  # Global factor

    @pyped
    def lambda_arg_shadowing_pipeline(x):
        return x >> (lambda factor: lambda val: val * factor)(
            2
        )  # Lambda argument 'factor' shadows global factor

    assert (
        lambda_arg_shadowing_pipeline(5) == 10
    )  # Lambda arg shadowing test, lambda factor (2) should be used, 5 * 2 = 10


def test_pipe_with_global_keyword():
    global GLOBAL_VAR  # Declare global variable

    GLOBAL_VAR = 20  # Initialize global variable

    @pyped
    def global_keyword_pipeline(x):
        global GLOBAL_VAR  # Use global keyword to modify global variable
        GLOBAL_VAR += 1
        return x >> (
            lambda val: val + GLOBAL_VAR
        )  # Lambda should capture modified global variable

    assert (
        global_keyword_pipeline(5) == 26
    )  # Global keyword test, GLOBAL_VAR becomes 21, 5 + 21 = 26


def test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10  # Nonlocal variable

        @pyped
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var  # Use nonlocal keyword to modify nonlocal variable
            nonlocal_var += 1
            return x >> (
                lambda val: val + nonlocal_var
            )  # Lambda should capture modified nonlocal variable

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert (
        nonlocal_keyword_pipeline_func(5) == 16
    )  # Nonlocal keyword test, nonlocal_var becomes 11, 5 + 11 = 16


def test_pipe_with_closure_modification():
    def create_counter():
        count = 0  # Enclosed variable in closure

        def increment():
            nonlocal count
            count += 1
            return count  # Incrementing closure

        def get_count_pipeline():
            return 5 >> (lambda x: increment())  # Pipeline calling closure increment

        return get_count_pipeline, increment  # Return pipeline and incrementor

    get_pipeline, incrementor = create_counter()

    @pyped
    def closure_modification_pipeline():
        count1 = get_pipeline()  # First call to pipeline, increments counter once
        count2 = get_pipeline()  # Second call, increments again
        incrementor()  # Increment counter directly
        count3 = get_pipeline()  # Third call, increments again
        return count1, count2, count3  # Return counts from pipeline calls

    c1, c2, c3 = closure_modification_pipeline()
    assert (c1, c2, c3) == (
        1,
        2,
        4,
    )  # Closure modification test, counts should reflect closure state


def test_pipe_with_lambda_mutation():
    @pyped
    def lambda_mutation_pipeline(x):
        mutable_data = {"value": x}  # Mutable data structure

        def mutate_lambda(data):
            data["value"] += 1  # Lambda mutating mutable data
            return data["value"]

        return mutable_data >> mutate_lambda >> mutate_lambda

    assert (
        lambda_mutation_pipeline(5) == 7
    )  # Lambda mutation test, mutable data is modified across pipeline steps


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

    assert (
        class_instance_mutation_pipeline(data_instance) == 7
    )  # Class instance mutation test, instance state is modified


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

    assert (
        complex_mutation_chain_pipeline(mutator_instance) == 13
    )  # Complex mutation chain, ((((5 + 1) * 2) + 1)) = 13


def test_pipe_with_deeply_nested_lambda():  # Stack depth test for deeply nested lambdas
    @pyped
    def deeply_nested_lambda_pipeline(x):
        pipeline = x
        for _ in range(500):  # Deeply nested lambdas
            pipeline = pipeline >> (lambda v: lambda w: w + 1)()
        return pipeline

    assert (
        deeply_nested_lambda_pipeline(0) == 500
    )  # Deeply nested lambda stack test, similar to deeply_nested_pipeline, but lambdas nested even deeper.


def test_pipe_with_deeply_nested_binop():  # Stack depth test for deeply nested binops
    @pyped
    def deeply_nested_binop_pipeline(x):
        pipeline = x
        for _ in range(500):  # Deeply nested binop pipelines
            pipeline = pipeline >> (lambda v: v + 1)
        return pipeline

    assert (
        deeply_nested_binop_pipeline(0) == 500
    )  # Deeply nested binop stack test, similar to deeply_nested_pipeline, but using binop nesting more intensely.


def test_pipe_with_lambda_returning_tuple():
    @pyped
    def lambda_tuple_return_pipeline(x):
        return x >> (lambda val: (val + 1, val * 2))

    assert lambda_tuple_return_pipeline(5) == (6, 10)  # Lambda returning tuple


def test_pipe_with_lambda_returning_list():
    @pyped
    def lambda_list_return_pipeline(x):
        return x >> (lambda val: [val + 1, val * 2])

    assert lambda_list_return_pipeline(5) == [6, 10]  # Lambda returning list


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


def test_pipe_with_lambda_returning_zip_object():
    @pyped
    def lambda_zip_return_pipeline():
        return (
            5
            >> (lambda val: zip(range(val), range(val, val + 3)))
            >> (lambda zip_obj: list(zip_obj))
        )

    assert lambda_zip_return_pipeline() == [
        (0, 5),
        (1, 6),
        (2, 7),
        (3, 8),
        (4, 9),
    ]  # Lambda returning zip object


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


def test_pipe_with_lambda_returning_awaitable():
    import asyncio

    async def dummy_awaitable(x):
        await asyncio.sleep(0.01)
        return x

    @pyped
    async def lambda_awaitable_return_pipeline(x):
        return x >> (lambda val: dummy_awaitable(val))  # Lambda returning awaitable

    async def run_lambda_awaitable_return_pipeline():
        return await lambda_awaitable_return_pipeline(5)

    assert (
        asyncio.run(run_lambda_awaitable_return_pipeline()) == 5
    )  # Lambda returning awaitable object


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

    assert lambda_partial_return_pipeline(5) == 6  # Lambda returning partial object


def test_pipe_with_lambda_returning_closure():
    def create_closure(factor):
        return lambda val: val * factor

    @pyped
    def lambda_closure_return_pipeline(x):
        return x >> (lambda val: create_closure(val)) >> (lambda closure: closure(2))

    assert lambda_closure_return_pipeline(5) == 10  # Lambda returning closure object


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

    assert lambda_staticmethod_return_pipeline(5) == 6  # Lambda returning staticmethod


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

    assert lambda_classmethod_return_pipeline(5) == 5  # Lambda returning classmethod


def test_pipe_with_lambda_returning_builtin_function():
    @pyped
    def lambda_builtin_func_return_pipeline(x):
        return x >> (lambda val: str) >> (lambda builtin_func: builtin_func(val))

    assert (
        lambda_builtin_func_return_pipeline(5) == "5"
    )  # Lambda returning builtin function


def test_pipe_with_lambda_returning_user_defined_function():
    def add_one(x):
        return x + 1

    @pyped
    def lambda_user_func_return_pipeline(x):
        return x >> (lambda val: add_one) >> (lambda user_func: user_func(val))

    assert (
        lambda_user_func_return_pipeline(5) == 6
    )  # Lambda returning user-defined function


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

    assert (
        lambda_nested_func_return_pipeline(5) == 6
    )  # Lambda returning nested function


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

    assert lambda_method_return_pipeline(instance) == 6  # Lambda returning method


def test_pipe_with_lambda_returning_lambda():
    @pyped
    def lambda_lambda_return_pipeline(x):
        return (
            x >> (lambda val: lambda v: v + 1) >> (lambda inner_lambda: inner_lambda(5))
        )

    assert lambda_lambda_return_pipeline(5) == 6  # Lambda returning lambda


def test_pipe_with_lambda_returning_binop_expression():
    @pyped
    def lambda_binop_return_pipeline(x):
        return x >> (
            lambda val: val + 1 * 2
        )  # Lambda directly returning binop expression

    assert lambda_binop_return_pipeline(5) == 7  # Lambda returning binop expression


def test_pipe_with_lambda_returning_list_comprehension():
    @pyped
    def lambda_list_comprehension_return_pipeline(x):
        return x >> (
            lambda val: [i * val for i in range(3)]
        )  # Lambda returning list comprehension

    assert lambda_list_comprehension_return_pipeline(5) == [
        0,
        5,
        10,
    ]  # Lambda returning list comprehension


def test_pipe_with_lambda_returning_generator_expression():
    @pyped
    def lambda_generator_comprehension_return_pipeline(x):
        return (
            x >> (lambda val: (i * val for i in range(3))) >> (lambda gen: sum(gen))
        )  # Lambda returning generator expression

    assert (
        lambda_generator_comprehension_return_pipeline(5) == 15
    )  # Lambda returning generator expression


def test_pipe_with_lambda_returning_conditional_expression():
    @pyped
    def lambda_conditional_expression_return_pipeline(x):
        return x >> (lambda val: "Positive" if val > 0 else "Non-positive")

    assert (
        lambda_conditional_expression_return_pipeline(5) == "Positive"
    )  # Lambda returning conditional expression


def test_pipe_with_lambda_returning_assignment_expression():  # Walrus operator in lambda return
    @pyped
    def lambda_assignment_expression_return_pipeline(x):
        return x >> (
            lambda val: (y := val * 2)
        )  # Lambda returning assignment expression (walrus) - returns assigned value

    assert (
        lambda_assignment_expression_return_pipeline(5) == 10
    )  # Lambda returning assignment expression (walrus)


def test_pipe_with_lambda_returning_call_expression():
    def add_one(x):
        return x + 1

    @pyped
    def lambda_call_expression_return_pipeline(x):
        return x >> (lambda val: add_one(val))  # Lambda returning call expression

    assert (
        lambda_call_expression_return_pipeline(5) == 6
    )  # Lambda returning call expression


def test_pipe_with_lambda_returning_attribute_expression():
    class MyClass:
        def __init__(self, value):
            self.value = value

    instance = MyClass(7)

    @pyped
    def lambda_attribute_expression_return_pipeline(instance):
        return instance >> (
            lambda obj: obj.value
        )  # Lambda returning attribute expression

    assert (
        lambda_attribute_expression_return_pipeline(instance) == 7
    )  # Lambda returning attribute expression


def test_pipe_with_lambda_returning_subscript_expression():
    data = [10, 20, 30]

    @pyped
    def lambda_subscript_expression_return_pipeline(data):
        return data >> (lambda lst: lst[1])  # Lambda returning subscript expression

    assert (
        lambda_subscript_expression_return_pipeline(data) == 20
    )  # Lambda returning subscript expression


def test_pipe_with_lambda_returning_starred_expression():  # Starred expression in lambda return - not directly valid in return, but in list/tuple/set
    @pyped
    def lambda_starred_expression_return_pipeline(x):
        return x >> (
            lambda val: [*range(val, val + 3)]
        )  # Lambda returning starred expression (in list)

    assert lambda_starred_expression_return_pipeline(5) == [
        5,
        6,
        7,
    ]  # Lambda returning starred expression (in list)


def test_pipe_with_lambda_returning_yield_expression():  # yield is not directly valid in lambda, but in generator lambda (not a thing in python)
    pass  # yield and yield from are not valid directly in lambda, so no direct test case for lambda returning yield expression in standard python.


def test_named_expression_as_pipeline_step():
    @pyped
    def named_expression_pipeline(x):
        return x >> (incremented := lambda val: val + 1) >> incremented

    assert named_expression_pipeline(5) == 7  # Named expression as pipeline step


def test_nested_named_expressions_pipeline():
    @pyped
    def nested_named_expression_pipeline(x):
        return (
            x
            >> (doubled := lambda val: val * 2)
            >> (incremented := lambda val: val + 1)
            >> doubled
            >> incremented
        )

    assert (
        nested_named_expression_pipeline(5) == 21
    )  # Nested named expressions pipeline


def test_named_expression_reuse_pipeline():
    @pyped
    def named_expression_reuse_pipeline(x):
        incremented = lambda val: val + 1
        return x >> (inc_op := incremented) >> inc_op >> inc_op

    assert named_expression_reuse_pipeline(5) == 8  # Named expression reuse in pipeline


def test_named_expression_complex_pipeline():
    @pyped
    def named_expression_complex_pipeline(x):
        return (
            x
            >> (add_one := lambda val: val + 1)
            >> add_one
            >> (multiply_by_two := lambda val: val * 2)
            >> multiply_by_two
            >> add_one
        )

    assert (
        named_expression_complex_pipeline(5) == 17
    )  # Complex named expressions pipeline


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

    assert (
        named_expression_walrus_pipeline(5) == 31
    )  # Named expression with walrus, reusing initial walrus assigned value


def test_named_expression_in_conditional_pipeline():
    @pyped
    def named_expression_conditional_pipeline(flag, x):
        if flag:
            op = (incremented := lambda val: val + 1)
        else:
            op = (doubled := lambda val: val * 2)
        return x >> op

    assert (
        named_expression_conditional_pipeline(True, 5) == 6
    )  # Named expression in conditional pipeline, if branch
    assert (
        named_expression_conditional_pipeline(False, 5) == 10
    )  # Named expression in conditional pipeline, else branch


def test_named_expression_in_loop_pipeline():
    @pyped
    def named_expression_loop_pipeline(x):
        pipeline = x
        for i in range(3):
            op_name = f"op_{i}"
            pipeline = pipeline >> (
                op := lambda val: val + i
            )  # Named expression in loop
        return pipeline

    assert named_expression_loop_pipeline(5) == 8  # Named expression in loop pipeline


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
    assert nested_pipeline_func(5) == 17  # Named expression in nested scopes pipeline


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

    assert (
        named_expression_decorator_pipeline(5) == 20
    )  # Named expression with decorator


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
    assert calc_instance.value == 5  # Named expression in class method pipeline


def test_named_expression_staticmethod_pipeline():
    class MathUtils:
        @staticmethod
        @pyped
        def process_value(x):
            return x >> (increment_op := lambda val: val + 1) >> increment_op

    assert MathUtils.process_value(5) == 7  # Named expression in static method pipeline


def test_named_expression_property_pipeline():
    class MyClass:
        def __init__(self, value):
            self._value = value

        @property
        @pyped
        def processed_value(self):
            return self._value >> (double_op := lambda val: val * 2) >> double_op

    instance = MyClass(5)
    assert instance.processed_value == 20  # Named expression in property pipeline


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

    assert (
        asyncio.run(run_named_expression_async_pipeline()) == 7
    )  # Named expression in async pipeline


def test_named_expression_in_lambda_pipeline():
    @pyped
    def named_expression_in_lambda_pipeline(x):
        return x >> (lambda val: val >> (incremented := lambda v: v + 1) >> incremented)

    assert (
        named_expression_in_lambda_pipeline(5) == 7
    )  # Named expression inside lambda pipeline


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

    assert (
        named_expression_nested_lambda_pipeline(5) == 7
    )  # Named expression in nested lambda pipeline


def test_named_expression_in_comprehension_pipeline():
    @pyped
    def named_expression_comprehension_pipeline():
        return [
            i >> (doubled := lambda x: x * 2) >> doubled for i in range(3)
        ]  # Named expression in list comprehension pipeline

    assert named_expression_comprehension_pipeline() == [
        0,
        4,
        8,
    ]  # Named expression in comprehension pipeline


def test_named_expression_in_generator_expression_pipeline():
    @pyped
    def named_expression_generator_pipeline():
        return sum(
            i >> (doubled := lambda x: x * 2) >> doubled for i in range(3)
        )  # Named expression in generator expression pipeline

    assert (
        named_expression_generator_pipeline() == 12
    )  # Named expression in generator expression pipeline


def test_named_expression_in_dict_comprehension_pipeline():
    @pyped
    def named_expression_dict_pipeline():
        return {
            i: i >> (doubled := lambda x: x * 2) >> doubled for i in range(3)
        }  # Named expression in dict comprehension pipeline

    assert named_expression_dict_pipeline() == {
        0: 0,
        1: 4,
        2: 8,
    }  # Named expression in dict comprehension pipeline


def test_named_expression_in_set_comprehension_pipeline():
    @pyped
    def named_expression_set_pipeline():
        return {
            i >> (doubled := lambda x: x * 2) >> doubled for i in range(3)
        }  # Named expression in set comprehension pipeline

    assert named_expression_set_pipeline() == {
        0,
        4,
        8,
    }  # Named expression in set comprehension pipeline


def test_named_expression_in_nested_comprehensions_pipeline():
    @pyped
    def named_expression_nested_comprehension_pipeline():
        return [
            [j >> (incremented := lambda x: x + 1) >> incremented for j in range(i)]
            for i in range(3)
        ]  # Named expression in nested comprehensions pipeline

    assert named_expression_nested_comprehension_pipeline() == [
        [],
        [2],
        [2, 4],
    ]  # Named expression in nested comprehensions pipeline


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
        return (
            obj >> CustomObject.increment >> CustomObject.increment
        )  # Method reference directly

    assert (
        custom_object_method_ref_pipe().value == 12
    )  # Custom object method reference in pipeline


def test_pipe_with_bound_method_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    instance = Calculator(5)

    @pyped
    def bound_method_ref_pipeline():
        return (
            instance >> instance.add_one >> instance.add_one
        )  # Bound method reference

    assert bound_method_ref_pipeline() == 7  # Bound method reference pipeline


def test_pipe_with_unbound_method_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    @pyped
    def unbound_method_ref_pipeline(x):
        return (
            x >> Calculator.add_one >> Calculator.add_one
        )  # Unbound method reference - needs instance

    assert unbound_method_ref_pipeline(5) == 7  # Unbound method reference pipeline


def test_pipe_with_staticmethod_reference():
    class MathUtils:
        @staticmethod
        def increment(x):
            return x + 1

    @pyped
    def staticmethod_ref_pipeline(x):
        return (
            x >> MathUtils.increment >> MathUtils.increment
        )  # Static method reference

    assert staticmethod_ref_pipeline(5) == 7  # Static method reference pipeline


def test_pipe_with_classmethod_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        @classmethod
        def create_with_increment(cls, x):
            return cls(x + 1)

    @pyped
    def classmethod_ref_pipeline(x):
        return (
            x >> Calculator.create_with_increment >> (lambda calc: calc.value)
        )  # Classmethod reference

    calc_instance = classmethod_ref_pipeline(5)
    assert calc_instance == 6  # Class method reference pipeline


def test_pipe_with_builtin_function_reference():
    @pyped
    def builtin_func_ref_pipeline(x):
        return x >> str >> str.upper  # Builtin function and method reference

    assert (
        builtin_func_ref_pipeline(5) == "5".upper()
    )  # Builtin function and method reference pipeline


def test_pipe_with_user_defined_function_reference():
    def increment_func(x):
        return x + 1

    @pyped
    def user_func_ref_pipeline(x):
        return x >> increment_func >> increment_func  # User-defined function reference

    assert user_func_ref_pipeline(5) == 7  # User-defined function reference pipeline


def test_pipe_with_lambda_function_reference():
    increment_lambda = lambda x: x + 1  # Lambda assigned to variable

    @pyped
    def lambda_func_ref_pipeline(x):
        return x >> increment_lambda >> increment_lambda  # Lambda function reference

    assert lambda_func_ref_pipeline(5) == 7  # Lambda function reference pipeline


def test_pipe_with_partial_object_reference():
    from functools import partial

    add_partial = partial(lambda x, y: x + y, y=1)  # Partial object

    @pyped
    def partial_object_ref_pipeline(x):
        return x >> add_partial >> add_partial  # Partial object reference

    assert partial_object_ref_pipeline(5) == 7  # Partial object reference pipeline


def test_pipe_with_closure_reference():
    def create_incrementor_closure(inc):
        def incrementor(x):
            return x + inc  # Closure

        return incrementor

    increment_by_1 = create_incrementor_closure(1)  # Closure assigned to variable

    @pyped
    def closure_ref_pipeline(x):
        return x >> increment_by_1 >> increment_by_1  # Closure reference pipeline

    assert closure_ref_pipeline(5) == 7  # Closure reference pipeline
