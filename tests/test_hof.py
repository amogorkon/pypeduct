import itertools

import pytest

from pypeduct import PipeTransformError, pyped

# =====================
# Higher-Order Functions
# =====================


def test_hof_filter():
    @pyped
    def process_data(data: list[int]) -> list[int]:
        return data >> filter(lambda x: x % 2 == 0) >> list

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
    @pyped
    def custom_usage():
        return [1, 2, 3, 4, 5, 6, 3, 8] >> filter(lambda x: x > 5) >> list

    assert custom_usage() == [6, 8]  # filter(<lambda>, [1,6,2,8])


# =====================
# ... Placeholder Tests
# =====================


def test_placeholder_failure():
    with pytest.raises(PipeTransformError):

        @pyped
        def math_operations():
            return 5 >> pow(..., ...)

        math_operations()


def test_placeholder_positional_left():
    @pyped
    def math_operations():
        return 5 >> pow(..., 2)  # Should become pow(5, 2)

    assert math_operations() == 25


def test_placeholder_positional_right():
    @pyped
    def math_operations():
        return 5 >> pow(2, ...)  # Should become pow(2, 5)

    assert math_operations() == 32


def test_placeholder_keyword():
    @pyped
    def config_processing():
        return {"a": 1} >> print(..., flush=True)

    # Should capture output: {"a": 1} with flush=True
    # (Just testing execution, not return value)
    config_processing()


def test_placeholder_no_unpacking():
    @pyped
    def tuple_handling():
        return (1, 2) >> sum(...)  # sum((1,2)) not sum(1,2)

    assert tuple_handling() == 3


def test_placeholder_multiple_placeholders():
    with pytest.raises(PipeTransformError):

        @pyped
        def invalid_usage():
            return 5 >> max(..., ...)

        invalid_usage()


def test_placeholder_on_the_left_lazy():
    @pyped
    def real_ellipsis_usage():
        return ... >> bool

    # function is lazyily decorated, exception is NOT raised


def test_placeholder_on_the_left():
    with pytest.raises(PipeTransformError):

        @pyped
        def real_ellipsis_usage():
            return ... >> bool  # no point in using ... like this, is there?

        real_ellipsis_usage()


# =====================
# Edge Cases
# =====================


def test_hof_with_tuple_data_1():
    @pyped
    def tuple_with_hof():
        return ((1, 2, 3),) >> zip([4, 5, 6]) >> list

    assert tuple_with_hof() == [(1, 4), (2, 5), (3, 6)]


def test_hof_with_tuple_data_2():
    @pyped
    def tuple_with_hof():
        return (1, 2, 3) >> zip(..., [4, 5, 6]) >> list

    assert tuple_with_hof() == [(1, 4), (2, 5), (3, 6)]


def test_placeholder_invalid_position():
    @pyped
    def bad_position():
        return 5 >> int(...)  # int(5)

    assert bad_position() == 5


def test_mixed_hof_and_placeholder():
    @pyped
    def complex_case():
        return [1, "2", 3] >> filter(..., key=str.isdigit) >> map(int) >> sum

    with pytest.raises(TypeError):  # filter() gets 2 args
        complex_case()


def test_custom_hof_registry():
    def reversed_filter(func, iterable):
        return filter(func, iterable)

    @pyped(add_hofs={"reversed_filter": reversed_filter})
    def custom_behavior():
        return range(10) >> reversed_filter(lambda x: x % 3 == 0)

    result = custom_behavior()
    assert list(result) == [0, 3, 6, 9]


def test_default_extension_qualname():
    @pyped(add_hofs={"itertools.starmap": itertools.starmap})
    def extended_defaults():
        return [(1, 2), (3, 4)] >> itertools.starmap(pow) >> list

    assert extended_defaults() == [1, 81]


def test_default_extension_shortname():
    starmap = itertools.starmap

    @pyped(add_hofs={"starmap": starmap})
    def extended_defaults():
        return [(1, 2), (3, 4)] >> starmap(pow) >> list

    assert extended_defaults() == [1, 81]
