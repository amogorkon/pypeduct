from pypeduct import pyped


def test_pipe_with_closure_reference():
    def create_incrementor_closure(inc):
        def incrementor(x):
            return x + inc

        return incrementor

    increment_by_1 = create_incrementor_closure(1)

    @pyped
    def closure_ref_pipeline(x):
        return x >> increment_by_1 >> increment_by_1

    assert closure_ref_pipeline(5) == 7
