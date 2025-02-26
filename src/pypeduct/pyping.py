from __future__ import annotations

import ast
import inspect
import linecache
from textwrap import dedent
from typing import Any, Callable, TypeVar

from pypeduct.transformer import PipeTransformer

T = TypeVar("T", bound=Callable[..., Any] | type[Any])

VERBOSE = False


def pyped(func_or_class: T | None = None) -> T | Callable[[T], T]:
    """Decorator transforming >>/<< operators into pipeline operations with configurable options."""

    caller_frame = inspect.currentframe()
    assert caller_frame is not None
    caller_frame = caller_frame.f_back
    assert caller_frame is not None
    ctx = {
        **caller_frame.f_globals,
        **caller_frame.f_locals,
    }
    # Capture closure variables from the original function
    if inspect.isfunction(func_or_class):
        closure = func_or_class.__closure__
        if closure is not None:
            free_vars = func_or_class.__code__.co_freevars
            for name, cell in zip(free_vars, closure):
                ctx[name] = cell.cell_contents

    try:
        source = inspect.getsource(func_or_class)
    except OSError:
        if not inspect.isfunction(func_or_class):
            raise

        code = func_or_class.__code__
        lines = linecache.getlines(code.co_filename)
        source = "".join(
            lines[
                code.co_firstlineno - 1 : code.co_firstlineno
                + code.co_code.co_argcount  # type: ignore
            ]
        )
        source = dedent(source.split(":", 1)[1].strip())

    transformer = PipeTransformer()

    tree = transformer.visit(ast.parse(dedent(source)))

    if VERBOSE:
        transformed_code = ast.unparse(tree)
        print(f"\n----- Transformed Code for: {func_or_class.__name__} -----")
        print(transformed_code)
        print("----- End Transformed Code -----\n")

    if inspect.iscoroutinefunction(func_or_class):
        ast.increment_lineno(tree, func_or_class.__code__.co_firstlineno - 1)

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
            node.decorator_list = []

    ast.fix_missing_locations(tree)
    code = compile(
        tree, filename=ctx.get("__file__", "<pyped>"), mode="exec", optimize=2
    )
    exec(code, ctx)
    return ctx[tree.body[0].name]
