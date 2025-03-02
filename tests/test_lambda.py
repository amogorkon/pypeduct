from __future__ import annotations

from pypeduct import pyped


def test_lambda_with_defaults_in_pipeline():
    @pyped
    def lambda_defaults_pipeline(x):
        return x >> (lambda val, *, inc=1: val + inc)

    assert lambda_defaults_pipeline(5) == 6


def test_lambda_with_kwargs_in_pipeline():
    @pyped
    def lambda_kwargs_pipeline(x, **kwargs):
        return x >> (lambda val: val + kwargs["inc"])

    assert lambda_kwargs_pipeline(5, inc=1) == 6


def test_lambda_with_varargs_in_pipeline():
    @pyped
    def lambda_varargs_pipeline(x):
        return x >> (lambda val, *args: val + sum(args))(1, 2, 3)

    assert lambda_varargs_pipeline(5) == 11


def test_lambda_no_args_with_input_pipe():
    @pyped
    def lambda_no_args_input_pipeline(x):
        return x >> (lambda _: 10)

    assert lambda_no_args_input_pipeline(5) == 10


def test_lambda_positional_only_args_pipe():
    @pyped
    def lambda_pos_only_pipeline(x):
        return x >> (lambda val, /, inc: val + inc)(inc=1)

    assert lambda_pos_only_pipeline(5) == 6


def test_lambda_keyword_only_args_pipe():
    @pyped
    def lambda_kw_only_pipeline(x):
        return x >> (lambda val, *, inc: val + inc)(inc=1)

    assert lambda_kw_only_pipeline(5) == 6


def test_lambda_mixed_args_complex_pipe():
    @pyped
    def lambda_mixed_complex_pipeline(x):
        return x >> (
            lambda pos_only, val, *, kw_only, **kwargs: pos_only
            + val
            + kw_only
            + sum(kwargs.values())
        )(1, kw_only=2, other=3, another=4)

    assert lambda_mixed_complex_pipeline(5) == 15


def test_lambda_in_pipeline():
    @pyped
    def lambda_pipeline(x):
        return x >> (lambda val: val * 2)

    assert lambda_pipeline(0) == 0
    assert lambda_pipeline(1) == 2


def test_lambda_capture_free_vars_pipe():
    factor = 3

    @pyped
    def capture_free_vars_pipeline(x):
        return x >> (lambda val: val * factor)

    assert capture_free_vars_pipeline(5) == 15


def test_lambda_closure_pipe():
    def create_multiplier(factor):
        return lambda val: val * factor

    multiplier = create_multiplier(3)

    @pyped
    def closure_pipeline(x):
        return x >> multiplier

    assert closure_pipeline(5) == 15


def test_pipe_with_lambda_returning_conditional_expression():
    @pyped
    def lambda_conditional_expression_return_pipeline(x):
        return x >> (lambda val: "Positive" if val > 0 else "Non-positive")

    assert lambda_conditional_expression_return_pipeline(5) == "Positive"


def test_pipe_with_lambda_function_reference():
    increment_lambda = lambda x: x + 1

    @pyped
    def lambda_func_ref_pipeline(x):
        return x >> increment_lambda >> increment_lambda

    assert lambda_func_ref_pipeline(5) == 7


def test_lambda_capture_free_vars_pipe():
    factor = 3

    @pyped
    def capture_free_vars_pipeline(x):
        return x >> (lambda val: val * factor)

    assert capture_free_vars_pipeline(5) == 15


def test_lambda_closure_pipe():
    def create_multiplier(factor):
        return lambda val: val * factor

    multiplier = create_multiplier(3)

    @pyped
    def closure_pipeline(x):
        return x >> multiplier

    assert closure_pipeline(5) == 15


def test_pipe_with_lambda_returning_lambda():
    @pyped
    def lambda_lambda_return_pipeline(x):
        return (
            x >> (lambda val: lambda v: v + 1) >> (lambda inner_lambda: inner_lambda(5))
        )

    assert lambda_lambda_return_pipeline(5) == 6
