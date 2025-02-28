from __future__ import annotations

from pypeduct import pyped


def test_pipe_with_decorated_function():
    def decorator(func):
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs) + 3

        return wrapper

    @decorator
    @pyped
    def decorated_func() -> int:
        result: int = 5 >> (lambda x: x * 2)
        return result

    assert decorated_func() == 13  # (5 * 2) + 3


def test_class_pipe_in_property():
    @pyped
    class MyClass:
        def __init__(self, value: int) -> None:
            self._value = value

        @property
        def value(self) -> str:
            return self._value >> str

    instance = MyClass(100)
    assert instance.value == "100"


def test_method_pipe_in_property():
    class MyClass:
        def __init__(self, value: int) -> None:
            self._value = value

        @property
        @pyped
        def value(self) -> str:
            return self._value >> str

    instance = MyClass(100)
    assert instance.value == "100"
