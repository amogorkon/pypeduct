"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10

        @pyped(verbose=False)
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var
            nonlocal_var += 1
            return x >> (lambda val: val + nonlocal_var)

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert nonlocal_keyword_pipeline_func(5) == 16


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(f" ↓↓↓↓↓↓↓ {name} ↓↓↓↓↓↓")
        print(inspect.getsource(func))
        func()
        print(f"↑↑↑↑↑↑ {name} ↑↑↑↑↑↑")
        print()
