from pyping import pyped


def test_pipe_with_kwargs_in_function():
    @pyped
    def kwargs_function() -> str:
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"

        left_result: str = "Alyz" << greet(greeting="Hi")
        right_result: str = "Alyz" >> greet(greeting="Hi")
        assert left_result == right_result
        return right_result

    assert kwargs_function() == "Hi, Alyz!"


test_pipe_with_kwargs_in_function()
