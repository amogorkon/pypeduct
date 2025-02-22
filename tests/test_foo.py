# test_pipe_transform.py

import ast
import asyncio
import sys
import unittest

from pipe_transformer import PipeTransformError, pipes


class TestPipeTransform(unittest.TestCase):
    def test_basic_pipe(self):
        @pipes
        def basic_pipe() -> list[str]:
            result = 5 >> str << list
            return result

        self.assertEqual(basic_pipe(), ["5"])

    def test_async_pipe(self):
        @pipes
        async def async_func() -> int:
            return 10 >> (lambda x: x * 2)

        result = asyncio.run(async_func())
        self.assertEqual(result, 20)

    def test_complex_types(self):
        @pipes
        def complex_pipe() -> tuple[str, int, int]:
            a: list[int] = [1, 2, 3]
            b: dict[str, int] = {"a": 1}
            c: tuple[int, int, int] = (1, 2, 3)
            return a >> len >> str, b >> len, c >> len

        self.assertEqual(complex_pipe(), ("3", 1, 3))

    def test_lshift_operator(self):
        @pipes
        def lshift_pipe() -> str:
            def concat(a, b):
                return f"{a}_{b}"

            result = "world" << concat << ("hello" >> str)
            return result

        self.assertEqual(lshift_pipe(), "hello_world")

    def test_rshift_operator(self):
        @pipes
        def rshift_pipe() -> str:
            def wrap(text):
                return f"<{text}>"

            result = "content" >> wrap
            return result

        self.assertEqual(rshift_pipe(), "<content>")

    def test_nested_pipes(self):
        @pipes
        def nested_pipes() -> int:
            result = (5 >> (lambda x: x + 2)) >> (lambda x: x * 3)
            return result

        self.assertEqual(nested_pipes(), 21)

    def test_complex_expression_pipe(self):
        @pipes
        def complex_expression_pipe() -> int:
            expr = (2 + 3) * 4
            result = expr >> (lambda x: x - 5)
            return result

        self.assertEqual(complex_expression_pipe(), 15)

    def test_await_in_pipe(self):
        @pipes
        async def await_pipe() -> str:
            async def async_upper(s):
                await asyncio.sleep(0.1)
                return s.upper()

            return await ("hello" >> async_upper)

        result = asyncio.run(await_pipe())
        self.assertEqual(result, "HELLO")

    def test_pipe_with_class_method(self):
        class MyClass:
            def __init__(self, value):
                self.value = value

            @pipes
            def multiply(self, x: int) -> int:
                return x * self.value

        instance = MyClass(3)
        result = 5 >> instance.multiply
        self.assertEqual(result, 15)

    def test_exception_handling_in_pipe(self):
        @pipes
        def exception_pipe():
            result = "test" >> int  # This should raise a ValueError
            return result

        with self.assertRaises(ValueError):
            exception_pipe()

    def test_syntax_error_in_pipes(self):
        faulty_code = """
@pipes
def syntax_error_func():
    result = 5 >>
    return result
"""
        with self.assertRaises(PipeTransformError) as context:
            exec(faulty_code, globals())
        self.assertIn("Syntax error", str(context.exception))

    def test_invalid_operator_transformation(self):
        @pipes
        def invalid_operator():
            result = 5 + (lambda x: x * 2)  # Should not be transformed
            return result

        self.assertIsInstance(invalid_operator(), type((lambda x: x * 2)))

    def test_transformer_error_propagation(self):
        original_visit_BinOp = ast.NodeTransformer.visit_BinOp

        def faulty_visit_BinOp(self, node):
            raise Exception("Simulated AST error")

        try:
            ast.NodeTransformer.visit_BinOp = faulty_visit_BinOp
            with self.assertRaises(PipeTransformError) as context:

                @pipes
                def faulty_transform():
                    result = 5 >> str
                    return result

            self.assertIn("AST transformation failed", str(context.exception))
        finally:
            ast.NodeTransformer.visit_BinOp = original_visit_BinOp

    def test_pipe_in_classmethod(self):
        class MyClass:
            @classmethod
            @pipes
            def class_method(cls, x: int) -> str:
                return x >> str

        result = MyClass.class_method(42)
        self.assertEqual(result, "42")

    def test_pipe_in_staticmethod(self):
        class MyClass:
            @staticmethod
            @pipes
            def static_method(x: int) -> str:
                return x >> str

        result = MyClass.static_method(42)
        self.assertEqual(result, "42")

    def test_pipe_in_property(self):
        class MyClass:
            def __init__(self, value):
                self._value = value

            @property
            @pipes
            def value(self) -> str:
                return self._value >> str

        instance = MyClass(100)
        self.assertEqual(instance.value, "100")

    def test_pipe_with_multiple_arguments_function(self):
        @pipes
        def multiple_args_func():
            def subtract(a, b):
                return a - b

            result = 10 << subtract << 3  # Equivalent to subtract(10, 3)
            return result

        self.assertEqual(multiple_args_func(), 7)

    def test_pipe_with_keyword_arguments(self):
        @pipes
        def keyword_args_func():
            def format_date(day, month, year):
                return f"{day}/{month}/{year}"

            day = 1
            month = 1
            year = 2020
            result = day << format_date << month << year
            return result

        self.assertEqual(keyword_args_func(), "1/1/2020")

    def test_pipe_with_generator_expression(self):
        @pipes
        def generator_pipe():
            def square(x):
                return x * x

            gen = (i for i in range(5))
            result = gen >> list >> (lambda lst: [square(x) for x in lst])
            return result

        self.assertEqual(generator_pipe(), [0, 1, 4, 9, 16])

    def test_pipe_with_partial_function(self):
        from functools import partial

        @pipes
        def partial_func_pipe():
            def multiply(a, b):
                return a * b

            multiply_by_two = partial(multiply, b=2)
            result = 5 >> multiply_by_two
            return result

        self.assertEqual(partial_func_pipe(), 10)

    def test_variable_scope_in_exec(self):
        @pipes
        def context_test():
            var = "hello"
            result = var >> str.upper
            return result

        self.assertEqual(context_test(), "HELLO")

    def test_compilation_failure_handling(self):
        original_compile = compile

        def faulty_compile(*args, **kwargs):
            raise SyntaxError("Simulated compilation error")

        try:
            sys.modules["builtins"].compile = faulty_compile
            with self.assertRaises(PipeTransformError) as context:

                @pipes
                def faulty_compilation():
                    result = 5 >> str
                    return result

            self.assertIn("Compilation failed", str(context.exception))
        finally:
            sys.modules["builtins"].compile = original_compile

    def test_custom_exception_message(self):
        faulty_code = """
@pipes
def invalid_syntax():
    return eval('invalid code')
"""
        with self.assertRaises(PipeTransformError) as context:
            exec(faulty_code, globals())
        self.assertIn("Could not retrieve source code", str(context.exception))

    def test_pipe_with_lambda(self):
        @pipes
        def lambda_test():
            result = 5 >> (lambda x: x * x)
            return result

        self.assertEqual(lambda_test(), 25)

    def test_pipe_with_decorated_function(self):
        def decorator(func):
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs) + 1

            return wrapper

        @pipes
        @decorator
        def decorated_func():
            result = 5 >> (lambda x: x * 2)
            return result

        self.assertEqual(decorated_func(), 11)  # (5 * 2) + 1

    def test_pipe_with_async_generator(self):
        @pipes
        async def async_generator_pipe():
            async def async_gen():
                for i in range(3):
                    yield i

            result = [i async for i in async_gen()] >> list
            return result

        result = asyncio.run(async_generator_pipe())
        self.assertEqual(result, [0, 1, 2])

    def test_pipe_with_custom_object(self):
        class CustomObject:
            def __init__(self, value):
                self.value = value

            def increment(self):
                self.value += 1
                return self

        @pipes
        def custom_object_pipe():
            obj = CustomObject(10)
            obj = obj >> CustomObject.increment >> CustomObject.increment
            return obj.value

        self.assertEqual(custom_object_pipe(), 12)

    def test_pipe_with_exception_in_function(self):
        @pipes
        def exception_in_function():
            def faulty_function(x):
                raise ValueError("Test exception")

            result = 5 >> faulty_function
            return result

        with self.assertRaises(ValueError):
            exception_in_function()

    def test_pipe_with_none(self):
        @pipes
        def none_pipe():
            result = None >> (lambda x: x is None)
            return result

        self.assertTrue(none_pipe())

    def test_pipe_with_type_annotations(self):
        @pipes
        def type_annotation_test() -> int:
            result: int = 5 >> (lambda x: x * 2)
            return result

        self.assertEqual(type_annotation_test(), 10)

    def test_pipe_with_kwargs_in_function(self):
        @pipes
        def kwargs_function():
            def greet(name, greeting="Hello"):
                return f"{greeting}, {name}!"

            result = "Alyz" << greet << {"greeting": "Hi"}
            return result

        self.assertEqual(kwargs_function(), "Hi, Alice!")

    def test_pipe_with_async_function_in_sync_context(self):
        @pipes
        def async_in_sync():
            async def async_double(x):
                return x * 2

            # Attempting to await in a sync function will raise an error
            result = 5 >> async_double
            return result

        with self.assertRaises(TypeError):
            async_in_sync()

    def test_pipe_with_multiple_pipes_in_one_expression(self):
        @pipes
        def multiple_pipes():
            result = 5 >> (lambda x: x + 1) >> (lambda x: x * 2) << (lambda x: x - 3)
            return result

        self.assertEqual(multiple_pipes(), 7)

    def test_pipe_with_property_decorator(self):
        class MyClass:
            def __init__(self, value):
                self._value = value

            @property
            @pipes
            def value(self) -> int:
                return self._value >> (lambda x: x * 2)

        instance = MyClass(10)
        self.assertEqual(instance.value, 20)

    def test_pipe_with_unary_operator(self):
        @pipes
        def unary_operator_test():
            result = (-5) >> abs
            return result

        self.assertEqual(unary_operator_test(), 5)

    def test_pipe_with_chained_comparisons(self):
        @pipes
        def chained_comparison_test(x: int) -> bool:
            return (1 < x < 10) >> (lambda x: x)

        self.assertTrue(chained_comparison_test(5))
        self.assertFalse(chained_comparison_test(0))


if __name__ == "__main__":
    unittest.main()
