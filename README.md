# pypeduct

pypeduct is a Python library for pipe transformations, inspired by Elixir-style pipelines.

## Features

- Transform functions and methods into pipelines
- Support for various Python constructs including lambdas, comprehensions, and more
- Exception handling within pipelines

## Installation

To install pypeduct, use pip:

```sh
pip install pypeduct
```

## Usage

Here's a basic example of how to use pypeduct:

```python
from pypeduct import pipe

@pipe
def add_one(x):
    return x + 1

@pipe
def multiply_by_two(x):
    return x * 2

result = 5 | add_one | multiply_by_two
print(result)  # Output: 12
```

## MAGIC

### Walrus Operator

The walrus operator (`:=`) is used to assign values to variables as part of an expression. This can be particularly useful in pipelines to capture intermediate results.

Example:

```python
from pypeduct import pyped

@pyped
def example_pipeline(x):
    def bar(x: int, /, *, baz: int) -> int:
        return x + baz

    x = (
        5
        >> (lambda x: x * 2)
        >> (y := bar(baz=1))
        >> (lambda x: x**2)
        >> (lambda x: x - 1)
        >> (lambda x: x / 2)
    )
    return x, y

print(example_pipeline(3))  # Output: (60.0, 11)
```

### Ellipsis (`...`) as Placeholder

The ellipsis (`...`) can be used as a placeholder in function definitions or pipelines. This allows for more flexible and readable code.

Example:

```python
from pypeduct import pyped

@pyped
def example_pipeline(x):
    return x >> (lambda y: y + 1) >> ... >> (lambda z: z * 2)

print(example_pipeline(3))  # Output: 8
```

### Partial Function Application

In pypeduct, using `func(3)` inside a pipeline is considered a partial application. This means that the function is partially applied with the given arguments and can be used in the pipeline.

Example:

```python
from pypeduct import pyped

@pyped
def example_pipeline(x):
    def add(a, b):
        return a + b

    return x >> add(3)

print(example_pipeline(2))  # Output: 5
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
