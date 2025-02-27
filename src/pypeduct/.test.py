from __future__ import annotations

from pyping import pyped


def test_class_pipe_in_property():
    @pyped(verbose=True)
    class MyClass:
        def __init__(self, value: int) -> None:
            self._value = value

        @property
        def value(self) -> str:
            return self._value >> str

    instance = MyClass(100)
    assert instance.value == "100", print(instance.value)
    print(instance.value)


test_class_pipe_in_property()
