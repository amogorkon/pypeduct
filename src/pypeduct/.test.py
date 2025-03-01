from __future__ import annotations

import inspect

from pyping import pyped

_ = pyped  # to avoid unused import warning

# ===========================================


def _test_nested_pipelines():
    @pyped(verbose=True)
    def nested_pipeline(x: int) -> int:
        return x >> (lambda val: val + 1 >> (lambda v: v * 2))

    assert nested_pipeline(5) == 12  # 5 + 1 = 6, 6 * 2 = 12


def _test_complex_walrus_pipeline():
    @pyped(verbose=True)
    def complex_walrus_pipeline(x):
        return (a := x) >> (
            lambda val: (b := val + 1) >> (lambda v: (c := v * 2, a + b + c))
        )

    assert complex_walrus_pipeline(5) == (12, 23)


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
