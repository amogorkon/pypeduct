from __future__ import annotations

from pypeduct import pyped


def test_pipeline_inside_conditional():
    @pyped
    def pipeline_inside_conditional(flag: bool) -> str:
        if flag:
            msg = "Hello" >> (lambda x: x + " World")
        else:
            msg = "Goodbye" >> (lambda x: x + " World")
        return msg

    assert pipeline_inside_conditional(True) == "Hello World"
    assert pipeline_inside_conditional(False) == "Goodbye World"


def test_pipeline_inside_conditional_walrus():
    @pyped
    def pipeline_in_conditional(flag: bool) -> str:
        if flag:
            (msg := "Hello") >> (lambda x: x + " World")
        else:
            (msg := "Goodbye") >> (lambda x: x + " World")
        return msg

    assert pipeline_in_conditional(True) == "Hello"  # Expect "Hello"
    assert pipeline_in_conditional(False) == "Goodbye"


def test_conditional_expression_pipeline():
    @pyped
    def conditional_pipeline(flag: bool) -> str:
        msg = "Hello" if flag else "Goodbye" >> (lambda x: x + " World")
        return msg

    assert conditional_pipeline(True) == "Hello"
    assert conditional_pipeline(False) == "Goodbye World"
