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

## Contributing

Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License

This project is licensed under the MIT License. See the LICENSE file for details.
