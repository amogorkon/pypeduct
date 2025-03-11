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


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(f" ↓↓↓↓↓↓↓ {name} ↓↓↓↓↓↓")
        print(inspect.getsource(func))
        func()
        print(f"↑↑↑↑↑↑ {name} ↑↑↑↑↑↑")
        print()
