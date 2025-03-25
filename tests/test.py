"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_tuple_unpacking_pipe():
    def unpack_tuple(x):
        return (*x, 4)

    @pyped(verbose=True)
    def tuple_unpack_pipeline(x):
        return x >> unpack_tuple

    assert tuple_unpack_pipeline((1, 2, 3)) == (
        1,
        2,
        3,
        4,
    )  # Tuple unpacking in pipeline


def test_pipe_with_tuple_concat():
    @pyped(verbose=True)
    def tuple_concat_pipeline():
        return (1, 2) >> (lambda x: x + (3, 4))

    assert tuple_concat_pipeline() == (1, 2, 3, 4)


def test_tuple_with_default_args():
    @pyped(verbose=True)
    def test_default_args() -> int:
        def add(x: int, y: int = 0) -> int:
            return x + y

        return (1,) >> add

    assert test_default_args() == 1


def test_variadic_function():
    @pyped(verbose=True)
    def test_variadic() -> int:
        def sum_all(*args: int) -> int:
            return sum(args)

        return (1, 2, 3) >> sum_all  # Should pass args as (1, 2, 3) => 6

    assert test_variadic() == 6


def test_namedtuple_inner_def_unpacking():
    from collections import namedtuple

    Point = namedtuple("Point", ["x", "y"])

    @pyped(verbose=True)
    def namedtuple_unpacking_pipeline():
        def add(x, y):
            return x + y

        point = Point(3, 4)
        return point >> add

    assert namedtuple_unpacking_pipeline() == 7


def test_pipe_with_mutable_default_argument():
    @pyped(verbose=True)
    def mutable_default_arg_pipeline():
        def func(val, mutable_list=[]):
            mutable_list.append(val)
            return val, mutable_list

        return 1 >> func >> func >> (lambda val, lst: lst)

    assert mutable_default_arg_pipeline() == [1, 1]


def test_decorator_stripping():
    def decorator(cls):
        cls.marked = True
        return cls

    @pyped(verbose=True)
    @decorator
    class TestClass:
        pass

    assert hasattr(TestClass, "marked"), "All decorators were stripped!"


def test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10

        @pyped(verbose=True)
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var
            nonlocal_var += 1
            return x >> (lambda val: val + nonlocal_var)

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert nonlocal_keyword_pipeline_func(5) == 16


def _test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10

        @pyped(verbose=True)
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var
            nonlocal_var += 1
            return x >> (lambda val: val + nonlocal_var)

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert nonlocal_keyword_pipeline_func(5) == 16


def _test_method_with_closure():
    def create_processor(scale: int):
        @pyped(verbose=True)
        class Processor:
            def process(self, x: int) -> int:
                return x >> (lambda y: y * scale)

        return Processor()

    processor = create_processor(3)
    assert processor.process(4) == 12, "Closure variable not captured!"


def _test_method_with_closure_():
    def create_processor(scale: int):
        @pyped
        class Processor:
            def process(self, x: int) -> int:
                return x >> (lambda y: y * scale)

        return Processor()

    processor = create_processor(3)
    assert processor.process(4) == 12, "Closure variable not captured!"


def _test_class_with_other_decorators():
    def validate(cls):
        cls.validated = True
        return cls

    @pyped(verbose=True)
    @validate
    class DataProcessor:
        def process(self, x: int) -> int:
            return x >> (lambda y: y + 1)

    # Check if @validate decorator was preserved
    assert hasattr(DataProcessor, "validated"), "Class lost other decorators!"
    # Check pipeline transformation
    assert DataProcessor().process(3) == 4


def test_pipe_with_mutable_default_argument():
    @pyped(verbose=True)
    def mutable_default_arg_pipeline():
        def func(val, mutable_list=[]):
            mutable_list.append(val)
            return val, mutable_list

        return 1 >> func >> func >> (lambda val, lst: lst)

    assert mutable_default_arg_pipeline() == [1, 1]


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(f" ↓↓↓↓↓↓↓ {name} ↓↓↓↓↓↓")
        print(inspect.getsource(func))
        func()
        print(f"↑↑↑↑↑↑ {name} ↑↑↑↑↑↑")
        print()
