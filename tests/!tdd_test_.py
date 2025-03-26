"""Tests for TDD, expected to fail."""

# prevent pytest from being removed by the formatter

import pytest as pytest

from pypeduct.pyping import pyped as pyped


def test_inheritance():
    @pyped
    class Base:
        def process(self, x: int) -> int:
            return x >> (lambda y: y + 1)

    class Child(Base):
        def process(self, x: int) -> int:
            return super().process(x) >> (lambda y: y * 2)

    assert Child().process(3) == (3 + 1) * 2, "Inheritance broken!"


def test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10

        @pyped
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var
            nonlocal_var += 1
            return x >> (lambda val: val + nonlocal_var)

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert nonlocal_keyword_pipeline_func(5) == 16
