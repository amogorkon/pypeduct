from __future__ import annotations

import ast
import inspect
import linecache
from functools import wraps
from textwrap import dedent
from typing import Any, Callable, TypeVar

from pypeduct.transformer import PipeTransformer

T = TypeVar("T", bound=Callable[..., Any] | type[Any])


def pyped(
    func_or_class: T | None = None, *, verbose: bool = False
) -> T | Callable[[T], T]:
    """Decorator transforming >>/<< operators into pipeline operations with optional verbosity."""

    def actual_decorator(func: T) -> T:
        transformed = None

        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal transformed
            if transformed is None:
                transformed = _transform_function(func, verbose)
            return transformed(*args, **kwargs)

        return wrapper  # type: ignore

    if func_or_class is None:
        return actual_decorator  # type: ignore
    else:
        return actual_decorator(func_or_class)  # type: ignore


def _transform_function(func: Callable, verbose: bool) -> Callable:
    """Performs the AST transformation using the original function's context."""

    ctx = {}
    if inspect.isfunction(func):
        ctx |= func.__globals__
        closure = func.__closure__
        if closure is not None:
            free_vars = func.__code__.co_freevars
            for name, cell in zip(free_vars, closure):
                ctx[name] = cell.cell_contents

    try:
        source = inspect.getsource(func)
        if verbose:
            print(f"\n----- Original Source for: {func.__name__} -----")
            print(dedent(source))
            print("----- End Original Source -----\n")
    except OSError:
        code = func.__code__
        lines = linecache.getlines(code.co_filename)
        source = "".join(
            lines[
                code.co_firstlineno - 1 : code.co_firstlineno + code.co_code.co_argcount
            ]  # type: ignore
        )
        source = dedent(source.split(":", 1)[1].strip())

    tree = PipeTransformer().visit(ast.parse(dedent(source)))

    top_level_node = tree.body[0]
    if isinstance(
        top_level_node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
    ):
        top_level_node.decorator_list = []

    ast.fix_missing_locations(tree)

    if verbose:
        transformed_code = ast.unparse(tree)
        print(f"\n----- Transformed Code for: {func.__name__} -----")
        print(transformed_code)
        print("----- End Transformed Code -----\n")

    exec(compile(tree, filename="<pyped>", mode="exec"), ctx)
    return ctx[func.__name__]
