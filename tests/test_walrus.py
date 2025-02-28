from __future__ import annotations

from pypeduct import pyped


def test_pipe_with_custom_object_walrus():
    class CustomObject:
        def __init__(self, value):
            self.value = value

        def increment(self, _):
            self.value += 1
            return self

        def foo(self, x: CustomObject) -> int:
            return x.value * 2

    @pyped
    def custom_object_pipe() -> int:
        return (obj := CustomObject(10)) >> obj.increment >> obj.increment >> obj.foo

    assert custom_object_pipe() == 24


def test_chained_walrus_assignments():
    @pyped
    def chained_walrus():
        (a := 1) >> (b := lambda x: x + 1) >> (c := lambda x: x * 2)
        return a, b, c

    assert chained_walrus() == (1, 2, 4)
