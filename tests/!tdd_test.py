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
