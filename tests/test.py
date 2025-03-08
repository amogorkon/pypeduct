"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def _test_keyword_args_pipeline():
    @pyped(verbose=True)
    def keyword_args_pipeline(x):
        return x >> (lambda val, factor=2: val * factor)

    assert keyword_args_pipeline(5) == 10  # 5 * 2 = 10


def _test_tuple_unpacking_pipe():
    def add(x: int, y: int) -> int:
        return x + y

    def multiply_and_add(x: int, y: int) -> int:
        return x * y, x + y

    @pyped(verbose=True)
    def multiple_assignments() -> int:
        return (1, 2) >> multiply_and_add >> add

    assert multiple_assignments() == 5  # (1*2), (1+2) => 2, 3 => 2 + 3 => 5


def test_variadic_function():
    @pyped(verbose=True)
    def test_variadic() -> int:
        def sum_all(*args: int) -> int:
            return sum(args)

        return (1, 2, 3) >> sum_all  # Should pass args as (1, 2, 3) => 6

    assert test_variadic() == 6


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
