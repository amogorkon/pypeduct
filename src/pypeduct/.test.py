from __future__ import annotations

from pyping import pyped


def test_pipeline_in_generator_expression():
    @pyped(verbose=True)
    def pipeline_in_generator() -> tuple[list[int], int]:
        gen = ((x := i) >> (lambda y: y * 2) for i in range(3))
        return list(gen), x

    result, last_x = pipeline_in_generator()
    assert result == [0, 2, 4]
    assert last_x == 2


test_pipeline_in_generator_expression()
