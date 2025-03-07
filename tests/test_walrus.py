from __future__ import annotations

from pypeduct import pyped


def test_chained_walrus_assignments():
    @pyped
    def chained_walrus():
        (a := 1) >> (b := lambda x: x + 1) >> (c := lambda x: x * 2)
        return a, b, c

    assert chained_walrus() == (1, 2, 4)


def test_complex_walrus_pipeline():
    @pyped
    def complex_walrus_pipeline(x):
        return (a := x) >> (
            lambda val: (b := val + 1) >> (lambda v: (c := v * 2, a + b + c))
        )

    assert complex_walrus_pipeline(5) == (12, 23)


def test_pipe_with_walrus_tower_kwargs():
    @pyped
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


def test_pipe_with_walrus_tower():
    @pyped
    def foo() -> tuple[float, int]:
        x = (
            5
            >> (lambda x: x * 2)
            >> (y := (lambda x: x + 1))
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )
        return x, y

    assert foo() == (60.0, 11)


def test_walrus_in_lambda_in_pipeline():
    @pyped
    def walrus_lambda_pipeline(x):
        return x >> (lambda val: (y := val * 2) + y)

    assert walrus_lambda_pipeline(5) == 20


def test_walrus_assignment_return_value():
    @pyped
    def walrus_return_pipeline(x):
        y = x >> (z := lambda val: val * 2)
        return y, z

    assert walrus_return_pipeline(5) == (10, 10)  # y = 10, returns (y, z)


def test_walrus_multiple_assignments():
    @pyped
    def walrus_multiple_assign_pipeline(x):
        return (a := x) >> (lambda val: (b := val + 1, a + b))

    assert walrus_multiple_assign_pipeline(5) == (6, 11)


def test_walrus_reset_in_pipeline():
    @pyped
    def walrus_reset_pipeline(x):
        x = 10
        return (x := 5) >> (lambda val: val + x)

    assert walrus_reset_pipeline(20) == 10


def test_walrus_tuple_passing():
    def return_tuple(x):
        return x, x * 2

    @pyped
    def walrus_tuple_unpack_pipeline(x):
        return x >> (t := return_tuple) >> (lambda t: t[0] + t[1])

    assert walrus_tuple_unpack_pipeline(5) == 15  # (a, b) = (5, 10), a + b = 15


def test_walrus_in_binop_pipeline():
    @pyped
    def walrus_binop_pipeline(x):
        return (x := 5) >> (lambda val: val + x)

    assert walrus_binop_pipeline(10) == 10


def test_walrus_assignment_in_return():
    @pyped
    def walrus_in_return_pipeline(x):
        return x >> (y := lambda val: val * 2)

    assert walrus_in_return_pipeline(5) == 10
