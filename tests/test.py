"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_tuple_unpacking_pipe():
    def add(x: int, y: int) -> int:
        return x + y

    def multiply_and_add(x: int, y: int) -> int:
        return x * y, x + y

    @pyped(verbose=True)
    def multiple_assignments() -> int:
        return (1, 2) >> multiply_and_add >> add

    assert multiple_assignments() == 5  # (1*2), (1+2) => 2, 3 => 2 + 3 => 5


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
