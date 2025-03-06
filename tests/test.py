"""WIP tests for pypeduct."""

from __future__ import annotations

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_pipe_with_custom_object_walrus():
    class CustomObject:
        def __init__(self, value: int) -> None:
            self.value = value

        def increment(self, _) -> CustomObject:
            self.value += 1
            return self

        def foo(self, x: CustomObject) -> int:
            return x.value * 2

    @pyped(verbose=True)
    def custom_object_pipe() -> int:
        return (obj := CustomObject(10)) >> obj.increment >> obj.increment >> obj.foo

    assert custom_object_pipe() == 24


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
