from pyping import pyped


def test_pipe_with_walrus():
    @pyped
    def foo():
        x = (
            5
            >> (lambda x: x * 2)
            >> (lambda x: x + 1) >> (y := )
            >> (lambda x: x**2)
            >> (lambda x: x - 1)
            >> (lambda x: x / 2)
        )

        print(y)
        return x

    return foo()


print(test_pipe_with_walrus())
