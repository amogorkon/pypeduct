# Pypeduct Pipeline Tuple Unpacking Specification

## 1. Introduction

This document details the tuple unpacking behavior within pypeduct pipelines, focusing on how sequences (tuples, lists) are handled when passed to functions using the pipe operator (`>>`).

## 2. Core Principle: Annotation-Controlled Unpacking

Pypeduct's tuple unpacking is governed by the following principle:

**Default to Unpacking, Control via First Argument Type Annotation - *Unless Overridden by Placeholder*.**

*   **Default Behavior: Unpack.**  When a sequence (tuple or list) is piped into a function, pypeduct will generally attempt to *unpack* the sequence elements as positional arguments to the function.
*   **Annotation Control: Prevent Unpacking with Sequence Type Hint.** You can prevent unpacking by explicitly annotating the *first positional argument* of the function with a **general sequence type**.
*   **Placeholder Override: Explicit `...` Disables Unpacking.** The argument position placeholder (`...`) provides the most direct control and **completely disables** the automatic tuple unpacking behavior based on type annotations.

## 3. Unpacking Decision Logic

The decision to unpack or not unpack a sequence passed via a pipeline is determined by the type annotation of the **first positional argument** of the function on the right side of the pipe (`>>`) **unless the argument position placeholder (`...`) is used.**

```mermaid
graph LR
    A[Start: Piped Value (Sequence)] --> B{Is Argument Position Placeholder (...) Used in Function Call?};
    B -- Yes --> C[**Placeholder Override: NO Unpacking based on Type Hint. Insert Value at ... Position**];
    B -- No --> D{Check First Argument's Type Annotation?};
    D -- Yes --> E{Is Annotation a General Sequence Type?};
    D -- No (No Annotation) --> F[Unpack (Default)];
    E -- Yes --> G[Do NOT Unpack];
    E -- No --> F[Unpack];
    F --> H[Function Called with Unpacked Arguments];
    G --> I[Function Called with Sequence as Single Argument];
    C --> J[Function Called with Value at Placeholder Position];
    H --> K[End: Function Call];
    I --> K;
    J --> K;
```

### 3.1. Rule: Check First Argument's Type Annotation (When Placeholder Not Used)

This rule only applies if the argument position placeholder (...) is not used in the function call.

Examine the Type Annotation:  Get the type annotation of the first positional argument of the function receiving the piped value.

Is it a General Sequence Type?  Determine if the annotation is one of the following "general sequence types":

* Sequence (from typing or collections.abc)
* List (from typing)
* Tuple (from typing)
* Iterable (from typing or collections.abc)
* list (built-in)
* tuple (built-in)

Unpack or Do Not Unpack:

* YES (First argument is annotated with a general sequence type): Do NOT Unpack. Pass the sequence from the left side of the pipe as a single argument to the function.
* NO (First argument has no annotation or is annotated with a non-sequence type): Unpack. Wrap the sequence from the left side of the pipe with a * (Starred expression) to unpack its elements as individual positional arguments to the function.

### 3.2. Example Scenarios (Type Annotation Controlled Unpacking)

#### 3.2.1. Unpacking (Default Behavior - Type Annotation Controlled)

```python
# No type annotations on function arguments (or non-sequence types)

# Lambda function (always unpacks - type annotation rule not applicable to lambdas, unless placeholder used)
(1, 2) >> (lambda x, y: x + y)  # Transforms to: (lambda x, y: x + y)((1, 2))

# Function defined with def (no annotations)
def add_numbers(a, b):
    return a + b

(3, 4) >> add_numbers  # Transforms to: add_numbers(*(3, 4))

# Function defined with def (non-sequence annotations)
def multiply_strings(text: str, count: int):
    return text * count

("hello", 3) >> multiply_strings # Transforms to: multiply_strings(*("hello", 3))
```

#### 3.2.2. No Unpacking (Sequence Type Annotation - Type Annotation Controlled)

```python
from typing import Sequence, List, Tuple

# Function annotated with Sequence
def process_sequence(items: Sequence):
    return len(items)

[10, 20, 30] >> process_sequence  # Transforms to: process_sequence([10, 20, 30]) # No unpack

# Function annotated with List
def process_list(item_list: List[int]):
    return sum(item_list)

(5, 6, 7) >> process_list  # Transforms to: process_list((5, 6, 7)) # No unpack

# Function annotated with Tuple
def handle_coordinates(points: Tuple[tuple[int, int], ...]):
    return [sum(p) for p in points]

[(1, 2), (3, 4)] >> handle_coordinates # Transforms to: handle_coordinates([(1, 2), (3, 4)]) # No unpack
```

## 4. Argument Position Placeholder (...) - Overrides Unpacking

Pypeduct provides an argument position placeholder, represented by the ellipsis symbol (...), to explicitly control where the value from the left side of the pipe (>>) is inserted within the arguments of the function on the right side. Crucially, the use of ... disables all automatic tuple unpacking based on type annotations.

### 4.1. Purpose of the Placeholder

The ... placeholder allows you to:

* Specify the exact argument position: Instead of relying on default unpacking or type-hint based behavior, you can use ... to force the piped value to be placed at a specific positional or keyword argument location.
* Explicit Control: Provides the most direct and unambiguous way to control argument placement, overriding any implicit unpacking rules.
* Flexibility: Useful when piping data into functions expecting input at non-first positions or when combining piped values with other arguments in a specific order, regardless of type hints.

### 4.2. Usage and Behavior

* Placement: The ... placeholder can be used in:
  * Positional arguments: Within the list of positional arguments in a function call.
  * Keyword argument values: As the value assigned to a keyword argument.
* Single Placeholder per Call:  Only one ... placeholder is allowed within a single function call in a pipeline expression. Using more than one placeholder will result in a PipeTransformError.
* Left Side Restriction: The ... placeholder is not allowed on the left side of the pipe (>>). It must always be used on the right side, within a function call.
* Insertion of Piped Value:  During transformation, the ... placeholder is replaced by the expression from the left side of the pipe, without any tuple unpacking applied.

### 4.3. Examples of Placeholder Usage (Unpacking Override)

#### 4.3.1. Placeholder in Positional Argument - Disables Unpacking

```python
from typing import Sequence

def process_data(items: Sequence, factor): # Sequence type hint would normally prevent unpacking
    return f"Processed {len(items)} items with factor {factor}"

# Placeholder forces insertion at first position, NO unpacking despite Sequence hint
(4, 5, 6) >> (lambda f: process_data(..., factor=f)) # Transforms to: (lambda f: process_data((4, 5, 6), factor=f))
# Even with Sequence hint, (4, 5, 6) is inserted as a tuple, not unpacked.

# Compare to no placeholder (with Sequence hint) - No unpacking (type hint behavior)
[1, 2, 3] >> process_data(factor=2) #  -> process_data([1, 2, 3], factor=2) # No unpack, Sequence hint is respected.
```

#### 4.3.2. Placeholder in Keyword Argument - Disables Unpacking

```python
def format_string(prefix, value, suffix=""):
    return f"{prefix}{value}{suffix}"

("Part:", "Data") >> (lambda suffix_str: format_string(prefix=..., value="info", suffix=suffix_str))
# Transforms to: (lambda suffix_str: format_string(prefix=("Part:", "Data"), value="info", suffix=suffix_str))
# Even if format_string had type hints suggesting unpacking for 'prefix', using '...' overrides and passes ("Part:", "Data") as-is to 'prefix'.
```

### 4.4. Error Cases (Placeholder Related)

#### 4.4.1. Placeholder on the Left Side (Error)

```python
# Invalid -  "..." on the left side is not allowed
# ... >> (lambda x: x + 1) # This will raise a PipeTransformError
```

#### 4.4.2. Multiple Placeholders (Error)

```python
def combine(a, b, c):
    return a + b + c

# Invalid - Only one "..." placeholder is allowed per function call
# (1, 2, 3) >> (lambda x, y, z: combine(..., ..., ...)) # This will raise a PipeTransformError
```

## 5. General Sequence Types Triggering "No Unpacking" (Type Hint Rule)

This section is relevant only when the argument position placeholder (...) is not used.

The following type hints are considered "general sequence types" and will prevent tuple unpacking when used as the annotation for the first positional argument of a function in a pypeduct pipeline:

* Sequence (from typing or collections.abc)
* List (from typing)
* Tuple (from typing)
* Iterable (from typing or collections.abc)
* list (built-in)
* tuple (built-in)

## 6. Conclusion

This specification comprehensively defines tuple unpacking and argument insertion in pypeduct pipelines.  The argument position placeholder (...) provides explicit control and disables the default annotation-based unpacking, offering users maximum flexibility in constructing their data processing pipelines.