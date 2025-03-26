"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_pipeline_in_nested_functions() -> int:
    @pyped(verbose=True)
    def outer_function() -> int:
        def inner_function() -> int:
            return (x := 5) >> (lambda y: y * y)

        return inner_function()

    assert outer_function() == 25


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(f" ↓↓↓↓↓↓↓ {name} ↓↓↓↓↓↓")
        print(inspect.getsource(func))
        func()
        print(f"↑↑↑↑↑↑ {name} ↑↑↑↑↑↑")
        print()
