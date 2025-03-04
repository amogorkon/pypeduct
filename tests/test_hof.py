import pytest

from pypeduct import pyped

# =====================
# Higher-Order Functions
# =====================


def test_hof_filter():
    @pyped
    def process_data(data: list[int]) -> list[int]:
        return data >> filter(lambda x: x % 2 == 0)

    assert process_data([1, 2, 3, 4]) == [2, 4]


def test_hof_chain():
    @pyped
    def process(data: list[int]) -> list[float]:
        return data >> filter(lambda x: x > 0) >> map(float) >> sorted

    assert process([-2, 3, 1]) == [1.0, 3.0]


def test_hof_non_standard_name():
    @pyped
    def demo():
        def myfilter(func, items):
            return [x for x in items if func(x)]

        return [1, 2, 3] >> myfilter(lambda x: x > 1)

    # Should NOT use data-last behavior for custom myfilter
    with pytest.raises(TypeError):
        demo()


def test_hof_with_placeholder():
    @pyped(verbose=True)
    def custom_usage():
        return (lambda x: x > 5) >> filter(..., [1, 6, 2, 8])

    assert custom_usage() == [6, 8]  # filter(<lambda>, [1,6,2,8])


# =====================
# ... Placeholder Tests
# =====================


def test_placeholder_positional():
    @pyped(verbose=True)
    def math_operations():
        return 5 >> pow(2, ...)  # Should become pow(2, 5)

    assert math_operations() == 32


def test_placeholder_keyword():
    @pyped(verbose=True)
    def config_processing():
        return {"a": 1} >> print(..., flush=True)

    # Should capture output: {"a": 1} with flush=True
    # (Just testing execution, not return value)
    config_processing()


def test_placeholder_no_unpacking():
    @pyped(verbose=True)
    def tuple_handling():
        return (1, 2) >> sum(...)  # sum((1,2)) not sum(1,2)

    assert tuple_handling() == 3


def test_placeholder_mixed_args():
    @pyped(verbose=True)
    def mixed_usage():
        return 10 >> range(..., 0, ...)  # range(10, 0, 10)

    assert list(mixed_usage()) == []


def test_placeholder_multiple_ellipsis():
    with pytest.raises(SyntaxError):

        @pyped
        def invalid_usage():
            return 5 >> max(..., ...)


def test_placeholder_actual_ellipsis():
    @pyped(verbose=True)
    def real_ellipsis_usage():
        return ... >> bool  # Should pass through real Ellipsis

    assert real_ellipsis_usage() is True


# =====================
# Edge Cases
# =====================


def test_hof_with_tuple_data():
    @pyped(verbose=True)
    def tuple_with_hof():
        return (1, 2, 3) >> zip([4, 5, 6]) >> list

    assert tuple_with_hof() == [(1, 4), (2, 5), (3, 6)]


def test_placeholder_invalid_position():
    @pyped(verbose=True)
    def bad_position():
        return 5 >> int(...)  # int(5)

    assert bad_position() == 5


def test_mixed_hof_and_placeholder():
    @pyped(verbose=True)
    def complex_case():
        return [1, "2", 3] >> filter(..., key=str.isdigit) >> map(int) >> sum

    with pytest.raises(TypeError):  # filter() gets 2 args
        complex_case()


import itertools


def test_custom_hof_registry():
    # Custom HOF that reverses argument order
    def reversed_filter(func, iterable):
        return filter(func, iterable)

    @pyped(add_hofs={reversed_filter}, extend_default_hofs=False)
    def custom_behavior():
        return range(10) >> reversed_filter(lambda x: x % 3 == 0)

    result = custom_behavior()
    assert list(result) == [0, 3, 6, 9], "Should use custom HOF argument order"


def test_default_extension():
    @pyped(add_hofs={itertools.starmap})
    def extended_defaults():
        return [(1, 2), (3, 4)] >> itertools.starmap(pow) >> list

    assert extended_defaults() == [1, 81], "Should handle starmap + keep defaults"


def test_complete_override():
    # Simulate HOF needing data as first arg
    @pyped(add_hofs=set(), extend_default_hofs=False)
    def no_special_handling():
        return [1, 2, 3] >> filter(lambda x: x > 1)

    with pytest.raises(TypeError):
        no_special_handling()  # filter() called as filter([1,2,3], lambda)
