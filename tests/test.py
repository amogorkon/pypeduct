"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_tuple_unpacking_lambda():
    @pyped(verbose=True)
    def multiple_assignments() -> int:
        return (1, 2) >> (lambda x, y: x + y)

    assert multiple_assignments() == 3


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
