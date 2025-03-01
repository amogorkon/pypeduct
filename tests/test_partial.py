from pypeduct import pyped


def test_pipe_with_partial_object_reference():
    from functools import partial

    add_partial = partial(lambda x, y: x + y, y=1)

    @pyped
    def partial_object_ref_pipeline(x):
        return x >> add_partial >> add_partial

    assert partial_object_ref_pipeline(5) == 7


def test_partial_application_pipeline():
    from functools import partial

    def multiply(x, y):
        return x * y

    double = partial(multiply, y=2)

    @pyped
    def partial_pipeline(x):
        return x >> double

    assert partial_pipeline(5) == 10
