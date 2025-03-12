"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_nested_class_transformation():
    @pyped(verbose=True)
    class Outer:
        class Inner:
            def process(self, x: int) -> int:
                return x >> (lambda y: y * 3)

    instance = Outer.Inner()
    assert instance.process(2) == 6, "Nested class method not transformed!"


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


def test_pipe_with_mutable_default_argument():
    @pyped
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
