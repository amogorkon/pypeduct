from pypeduct import pyped


def test_pipe_with_unbound_method_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def add_one(self, x):
            return x + 1

    @pyped
    def unbound_method_ref_pipeline(x):
        return x >> Calculator.add_one(None, ...) >> Calculator.add_one(None, ...)

    assert unbound_method_ref_pipeline(5) == 7


def test_pipe_with_closure_modification():
    def create_counter():
        count = 0

        def increment():
            nonlocal count
            count += 1
            return count

        @pyped
        def get_count_pipeline():
            return 5 >> (lambda x: increment())

        return get_count_pipeline, increment

    get_pipeline, incrementor = create_counter()

    def closure_modification_pipeline():
        count1 = get_pipeline()
        count2 = get_pipeline()
        incrementor()
        count3 = get_pipeline()
        return count1, count2, count3

    c1, c2, c3 = closure_modification_pipeline()
    assert (c1, c2, c3) == (1, 2, 4)


def test_pipe_with_bound_method_reference():
    class Calculator:
        def __init__(self, value):
            self.value = value

        def increment(self):
            self.value += 1
            return self

    @pyped
    def bound_method_ref_pipeline():  # Bound method reference
        return (
            Calculator(5)
            >> Calculator.increment
            >> Calculator.increment
            >> (lambda calc: calc.value)
        )

    assert bound_method_ref_pipeline() == 7


def test_named_expression_decorator_pipeline():
    def decorator_factory(factor):
        def decorator(func):
            def wrapper(val):
                return func(val) * factor

            return wrapper

        return decorator

    @pyped
    def named_expression_decorator_pipeline(x):
        @decorator_factory(2)
        def doubled(val):
            return val

        return x >> doubled

    assert named_expression_decorator_pipeline(5) == 10


def test_pipe_with_complex_mutation_chain():
    @pyped
    class DataMutator:
        def __init__(self, data):
            self.data = data

        def add_one(self):
            self.data["value"] += 1
            return self

        def multiply_by_two(self):
            self.data["value"] *= 2
            return self

        def get_value(self):
            return self.data["value"]

        def mutate_chain(self):
            return (
                self
                >> DataMutator.add_one
                >> DataMutator.multiply_by_two
                >> DataMutator.add_one
                >> DataMutator.get_value
            )

    mutator_instance = DataMutator({"value": 5})

    def complex_mutation_chain_pipeline(mutator):
        return mutator.mutate_chain()

    assert complex_mutation_chain_pipeline(mutator_instance) == 13


def test_with_statement_in_pipeline():
    class ContextManager:
        def __enter__(self):
            print("Entering context")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            print("Exiting context")

        def process(self, x):
            return x + 1

    @pyped
    def with_statement_pipeline(x):
        with ContextManager() as cm:
            return x >> cm.process

    assert with_statement_pipeline(5) == 6


def test_deeply_nested_pipeline():
    @pyped
    def deeply_nested_pipeline(x):
        pipeline = x
        for _ in range(500):
            pipeline = pipeline >> (lambda x, f: f(x))(lambda w: w + 1)
        return pipeline

    assert deeply_nested_pipeline(0) == 500


def test_pipe_with_loop_variable_capture():
    @pyped
    def loop_variable_capture_pipeline():
        funcs = []
        for i in range(3):
            funcs.append(lambda x: x + i)
        pipeline = 0
        for func in funcs:
            pipeline = pipeline >> func
        return pipeline

    assert loop_variable_capture_pipeline() == 6


def test_class_in_function():
    @pyped
    def outer_function():
        class Inner:
            def __init__(self, value):
                self.value = value

            def operate(self, x):
                return x + self.value

            def test(self):
                return 3 >> self.operate >> self.operate

        return Inner(5)

    instance = outer_function()
    result = instance.test()

    assert result == 13
