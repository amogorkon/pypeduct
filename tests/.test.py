from __future__ import annotations

import inspect

from pypeduct import pyped

_ = pyped  # to avoid unused import warning

# ===========================================


def test_pipe_with_walrus_tower_kwargs():
    @pyped(verbose=True)
    def foo() -> tuple[float, int]:
        def bar(x: int, /, *, baz: int) -> int:
            return x + baz

        return x, y

    assert foo() == (60.0, 11)


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
