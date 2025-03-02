import pytest

from pypeduct import pyped


def test_tuple_unpacking_lambda():
    @pyped
    def multiple_assignments() -> int:
        return (1, 2) >> (lambda x, y: x + y)

    assert multiple_assignments() == 3


def test_tuple_unpacking_function():
    @pyped(verbose=True)
    def multiple_assignments() -> tuple[int, int]:
        def add(x: int, y: int) -> int:
            return x + y

        return (1, 2) >> add

    assert multiple_assignments() == 3


def test_tuple_unpacking_pipe():
    def add(x: int, y: int) -> int:
        return x + y

    def multiply_and_add(x: int, y: int) -> int:
        return x * y, x + y

    @pyped(verbose=True)
    def multiple_assignments() -> tuple[int, int]:
        return (1, 2) >> multiply_and_add >> add

    assert multiple_assignments() == 5  # (1*2), (1+2) => 2, 3 => 2 + 3 => 5


def test_tuple_not_unpacked():
    @pyped
    def multiple_assignments() -> int:
        return (1, 2) >> (lambda x: x + 1)

    with pytest.raises(TypeError):
        multiple_assignments()


def test_tuple_unpacking_failure():
    @pyped
    def multiple_assignments() -> int:
        return (1, 2) >> (lambda x, y, z: x + 1)

    with pytest.raises(TypeError):
        multiple_assignments()


def test_tuple_with_default_args():
    @pyped(verbose=True)
    def test_default_args() -> int:
        def add(x: int, y: int = 0) -> int:
            return x + y

        return (1,) >> add  # Should unpack to (1, 0) => 1

    assert test_default_args() == 1


def test_variadic_function():
    @pyped(verbose=True)
    def test_variadic() -> int:
        def sum_all(*args: int) -> int:
            return sum(args)

        return (1, 2, 3) >> sum_all  # Should pass args as (1, 2, 3) => 6

    assert test_variadic() == 6
