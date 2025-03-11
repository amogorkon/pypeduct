from __future__ import annotations

from pypeduct import pyped


def test_pipe_in_comprehension():
    @pyped
    def comprehension_pipeline():
        return [i >> (lambda x: x * 2) for i in range(5)]

    assert comprehension_pipeline() == [0, 2, 4, 6, 8]


def test_pipe_in_generator_expression():
    @pyped
    def generator_pipeline():
        return sum(i >> (lambda x: x * 2) for i in range(5))

    assert generator_pipeline() == 20


def test_pipe_in_dict_comprehension():
    @pyped
    def dict_comprehension_pipeline():
        return {i: i >> (lambda x: x * 2) for i in range(3)}

    assert dict_comprehension_pipeline() == {
        0: 0,
        1: 2,
        2: 4,
    }


def test_pipe_in_set_comprehension():
    @pyped
    def set_comprehension_pipeline():
        return {i >> (lambda x: x * 2) for i in range(3)}

    assert set_comprehension_pipeline() == {0, 2, 4}


def test_nested_comprehensions_pipe():
    @pyped
    def nested_comprehension_pipeline():
        return [[j >> (lambda x: x + 1) for j in range(i)] for i in range(3)]

    assert nested_comprehension_pipeline() == [
        [],
        [1],
        [1, 2],
    ]


def test_generator_function_pipeline():
    def number_generator(n):
        for i in range(n):
            yield i

    @pyped
    def generator_func_pipeline():
        return number_generator(3) >> (lambda gen: list(gen))

    assert generator_func_pipeline() == [0, 1, 2]


def test_pipe_with_generator_comprehension():
    @pyped
    def generator_comprehension_pipeline():
        return (x * 2 for x in range(3)) >> (lambda gen: sum(gen))

    assert generator_comprehension_pipeline() == 6


def test_generator_expression_pipeline():
    @pyped
    def named_expression_generator_pipeline():
        return sum(i >> (lambda x: x * 2) for i in range(3))

    assert named_expression_generator_pipeline() == 6
