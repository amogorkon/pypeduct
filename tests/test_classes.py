from pypeduct import pyped


def test_nested_class_transformation():
    @pyped(verbose=True)
    class Outer:
        class Inner:
            def process(self, x: int) -> int:
                return x >> (lambda y: y * 3)

    instance = Outer.Inner()
    assert instance.process(2) == 6, "Nested class method not transformed!"


def test_method_with_closure():
    def create_processor(scale: int):
        @pyped
        class Processor:
            def process(self, x: int) -> int:
                return x >> (lambda y: y * scale)

        return Processor()

    processor = create_processor(3)
    assert processor.process(4) == 12, "Closure variable not captured!"


def test_inheritance():
    @pyped
    class Base:
        def process(self, x: int) -> int:
            return x >> (lambda y: y + 1)

    class Child(Base):
        def process(self, x: int) -> int:
            return super().process(x) >> (lambda y: y * 2)

    assert Child().process(3) == (3 + 1) * 2, "Inheritance broken!"


def test_class_pipe_in_property():
    @pyped
    class MyClass:
        def __init__(self, value: int) -> None:
            self._value = value

        @property
        def value(self) -> str:
            return self._value >> str

    instance = MyClass(100)
    assert instance.value == "100"


def test_class_decorator_pipe():
    @pyped
    class PipelineClass:
        def __init__(self, value):
            self.value = value

        def process(self):
            return self.value >> (lambda v: v + 1)

    instance = PipelineClass(5)
    assert instance.process() == 6


def test_pipe_with_classmethod_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        @classmethod
        def create_with_increment(cls, x):
            return cls(x + 1)

    @pyped
    def classmethod_ref_pipeline(x):
        return x >> Calculator.create_with_increment >> (lambda calc: calc.value)

    calc_instance = classmethod_ref_pipeline(5)
    assert calc_instance == 6


def test_pipe_with_staticmethod_reference():
    class MathUtils:
        @staticmethod
        def increment(x):
            return x + 1

    @pyped
    def staticmethod_ref_pipeline(x):
        return x >> MathUtils.increment >> MathUtils.increment

    assert staticmethod_ref_pipeline(5) == 7
