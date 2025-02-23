from pyping import pyped


@pyped
def test_function(x: int):
    return x >> str >> list >> len


print(test_function(123))
