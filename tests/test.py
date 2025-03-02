"""WIP tests for pypeduct."""

import inspect

from pypeduct import pyped as pyped

# ===========================================


def test_pipe_with_walrus_tower_kwargs():
    @pyped(verbose=True)
    def foo() -> tuple[float, int]:
        def bar(x: int, /, *, baz: int) -> int:
            return x + baz

        x = (
            5
            >> (lambda x: x * 2)
            >> (y := bar(baz=1))
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )
        return x, y

    assert foo() == (60.0, 11)


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
