from __future__ import annotations

import inspect

from pyping import pyped

_ = pyped  # to avoid unused import warning

# ===========================================


def _test_nested_class_transformation():
    @pyped(verbose=True)
    class Outer:
        class Inner:
            def process(self, x: int) -> int:
                return x >> (lambda y: y * 3)

    instance = Outer.Inner()
    assert instance.process(2) == 6, "Nested class method not transformed!"


def _test_nested_pipelines():
    @pyped(verbose=True)
    def nested_pipeline(x: int) -> int:
        return x >> (lambda val: val + 1 >> (lambda v: v * 2))

    assert nested_pipeline(5) == 12  # 5 + 1 = 6, 6 * 2 = 12


def test_lambda_with_kwargs_in_pipeline():
    @pyped(verbose=True)
    def lambda_kwargs_pipeline(x, **kwargs):
        return x >> (lambda val, **kwargs: val + kwargs["inc"])

    assert lambda_kwargs_pipeline(5, inc=1) == 6


# ===========================================

for name, func in globals().copy().items():
    if name.startswith("test_"):
        print(inspect.getsource(func))
        func()
