from __future__ import annotations

import inspect

from pypeduct import pyped

_ = pyped  # to avoid unused import warning

# ===========================================


def test_pipe_with_walrus_tower():
    @pyped(verbose=True)
    def foo() -> tuple[float, int]:
        def bar(x: int) -> int:
            return x + 1

        x = (
            5
            >> (lambda x: x * 2)
            >> (y := bar)
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
