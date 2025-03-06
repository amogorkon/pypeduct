# How to Use PyPeduct

## Introduction

Welcome to the PyPeduct how-to guide. This document will help you get started with PyPeduct, a Python library for data transformation and manipulation.

## Installation

To install PyPeduct, you can use pip:

```sh
pip install pypeduct
```

## Usage

### Importing the Library

To use PyPeduct, you first need to import it:

```python
import pypeduct
```

### Basic Example

Here is a basic example of how to use PyPeduct:

```python
from pypeduct import Transformer

# Create a transformer instance
transformer = Transformer()

# Define a simple transformation
transformer.add_step(lambda x: x * 2)

# Apply the transformation
result = transformer.transform([1, 2, 3, 4])
print(result)  # Output: [2, 4, 6, 8]
```

### Using the @pyped Decorator

The `@pyped` decorator allows you to create pipelines easily. Here are some examples:

#### Example 1: No Pipes

```python
from pypeduct import pyped

@pyped
def no_pipeline(x):
    return x + 1

print(no_pipeline(5))  # Output: 6
```

#### Example 2: External Function

```python
from pypeduct import pyped
import math

@pyped
def compute_square_root():
    return 16 >> math.sqrt

print(compute_square_root())  # Output: 4.0
```

#### Example 3: Built-in Function

```python
from pypeduct import pyped

@pyped
def compute_length():
    return [1, 2, 3] >> len

print(compute_length())  # Output: 3
```

#### Example 4: Walrus Operator with Keyword Arguments

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

## Examples

### Example 1: Data Cleaning

```python
from pypeduct import Transformer

# Create a transformer instance
transformer = Transformer()

# Define a data cleaning transformation
transformer.add_step(lambda x: x.strip())
transformer.add_step(lambda x: x.lower())

# Apply the transformation
result = transformer.transform(['  Hello ', 'WORLD  '])
print(result)  # Output: ['hello', 'world']
```

### Example 2: Data Aggregation

```python
from pypeduct import Transformer

# Create a transformer instance
transformer = Transformer()

# Define a data aggregation transformation
transformer.add_step(lambda x: sum(x))

# Apply the transformation
result = transformer.transform([[1, 2, 3], [4, 5, 6]])
print(result)  # Output: [6, 15]
```

### Example 3: Simple Difference

```python
from pypeduct import pyped

@pyped
def compute_difference():
    return 3 >> (lambda x: x - 1)

print(compute_difference())  # Output: 2
```

### Example 4: Recursive Function

```python
from pypeduct import pyped

@pyped
def recursive_pipeline(n):
    if n <= 0:
        return 0 >> (lambda x: x)
    else:
        return n >> (lambda x: x + recursive_pipeline(n - 1))

print(recursive_pipeline(5))  # Output: 15
```

### Example 5: Function with Default Arguments

```python
from pypeduct import pyped

@pyped
def compute():
    def add_numbers(x, y=10, z=5):
        return x + y + z

    return 5 >> add_numbers

print(compute())  # Output: 20
```

### Example 6: Function with Keyword-Only Arguments

```python
from pypeduct import pyped

@pyped
def process_data():
    def transform(data, *, scale=1):
        return [x * scale for x in data]

    return [1, 2, 3] >> transform

print(process_data())  # Output: [1, 2, 3]
```

### Example 7: Basic Pipe

```python
from pypeduct import pyped

@pyped
def basic_pipe() -> list[str]:
    result: list[str] = 5 >> str >> list
    return result

print(basic_pipe())  # Output: ["5"]
```

## Conclusion

This guide provided a basic overview of how to use PyPeduct. For more detailed information, please refer to the official documentation.
