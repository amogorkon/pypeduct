# pypeduct

PypeDuct is a Python 3 library for creating elegant and readable data processing pipelines, heavily inspired by the pipeline operator found in Elixir and Robin Hilliard's genius https://github.com/robinhilliard/pipes. It empowers you to chain operations together in a clear and sequential manner using the right-shift operator (`>>`), removing the need for nested function calls, substantially improving code readability and maintainability.

## Features

- **Pipeline Transformation:** Enables the transformation of functions and methods into seamless pipeline operations using the `>>` operator, which can also be used in a line-by-line manner as a "data processing tower".
- **Versatile Support:** Supports a wide range of Python constructs within pipelines, including regular functions, lambda expressions, classes and more.
- **Intermediate Value Capture:** Facilitates capturing intermediate results within pipelines using the walrus operator (`:=`).
- **Argument Placeholder:** Offers the ellipsis (`...`) as a flexible placeholder for argument insertion in pipeline stages.
- **Tuple Unpacking:** Provides intelligent tuple unpacking into function arguments by default, with an option to override using the placeholder.
- **Higher-Order Function Integration:** Seamlessly integrates with built-in higher-order functions like `map`, `filter`, and `reduce`, as well as custom higher-order functions.
- **Partial Function Application:** Partial function application within pipelines for more flexible and reusable code by default.

## Installation

To install pypeduct, simply use pip:

```sh
pip install pypeduct
```

## Usage

Here's a basic example of how to use pypeduct:

```python
from pypeduct import pyped

def add_one(x):
    return x + 1

def multiply_by_two(x):
    return x * 2
@pyped
def pipeline(x):
    return x >> add_one >> multiply_by_two

print(pipeline(5))  # Output: 12
```

## Magic!

### Walrus Operator

The walrus operator (`:=`) is used to assign intermediate results to variables as part of an expression. This can be particularly useful in pipelines to capture intermediate results. It differs from the regular behaviour in that it doesn't assign the current right-hand-side (=function) to the variable, but rather the return value of the function after it has been executed.
This can be a little confusing at first, but it's very powerful to capture intermediate results in a pipeline.

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

### Partial Function Application
Inside a pipeline, calls on the right hand side of the operator can be thought of as partial application. This means that the function call is "prepared" with the given arguments and the function then is finally called with the data that is piped into it. This is different from functools.partial in so far that there is no different (partial) function object created, but the arguments are assembled on the AST - the data from the left, the other arguments from the right. `data >> func(3)` is equivalent to `func(data, 3)`. This also works for methods and class instantiation, for positional and keyword arguments.

### Tuple Unpacking
Within a pipeline, tuples are automatically unpacked into function arguments. This means that `x,y >> lambda x,y: x+y` works as expected. This is the default behaviour and works with lambdas, functions, methods and classes. This is the default behaviour, but it can be overridden by using the ellipsis (`...`) as placeholder.

### Ellipsis (`...`) as Argument Position Indicator - Placeholder

The ellipsis (`...`) can be used as a placeholder in function definitions or pipelines. This allows for more flexible and readable code. This works for positional and keyword arguments.

Example:

```python
from pypeduct import pyped

@pyped
def pipeline(val):
    return val >> (lambda x, y: x - y)(2, ...)

print(pipeline(3))  # Output: -1
```

### Classes
Decorating a Class decorates all methods of the class. This is useful for classes that are used as a pipeline, where all methods are supposed to be pipeline stages. Inheritance is not supported. This is not a bug, but a feature, as it would lead to confusion and unexpected behaviour if a user subclasses a decorated class and tried to use the >> operator without knowing that the parent class was decorated.

Nested classes are supported. The decorator is applied to all methods of the class, including nested inner classes. This is useful for classes that are used as a pipeline, where all methods are supposed to be pipeline stages.

## Documentation
Check out our https://github.com/amogorkon/pypeduct/blob/main/docs/showcase.ipynb, our Pypeduct Pipeline Tuple Unpacking Specification at https://github.com/amogorkon/pypeduct/blob/main/docs/argument_unpacking_spec.md or the Howto https://github.com/amogorkon/pypeduct/blob/main/docs/howto.md and the over 350 test cases with more advanced examples!

Please report any inconsistencies or ideas for better examples or tests, it'll be greatly appreciated!

## Known Limitations

As exec() effectively hoists the code to the module-level, **nonlocal** statements become SyntaxErrors as there is no enclosing function scope to reference. This is the only known limitation of the library and will require some work to fix. If you need to use nonlocal variables, you can use a workaround by defining the function outside of the pipeline and then using it within the pipeline.

```
def test_pipe_with_nonlocal_keyword():
    def outer_function():
        nonlocal_var = 10

        @pyped
        def nonlocal_keyword_pipeline(x):
            nonlocal nonlocal_var
            nonlocal_var += 1
            return x >> (lambda val: val + nonlocal_var)

        return nonlocal_keyword_pipeline

    nonlocal_keyword_pipeline_func = outer_function()
    assert nonlocal_keyword_pipeline_func(5) == 16

E       SyntaxError: no binding for nonlocal 'nonlocal_var' found
```

## Contributing
Contributions are welcome! Please open an issue or submit a pull request on GitHub.

## License
This project is licensed under the MIT License. See the LICENSE file for details.


## Office Hours
You can contact me one-on-one! Check my [office hours](https://calendly.com/amogorkon/officehours) to set up a meeting :-)
