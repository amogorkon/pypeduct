from __future__ import annotations

import ast
import inspect
from textwrap import dedent
from typing import Any, Callable, Type, TypeVar

from pypeduct.transformer import PipeTransformer

T = TypeVar("T", bound=Callable[..., Any] | Type[Any])


def pyped(func_or_class: T) -> T:
    if inspect.isclass(func_or_class):
        decorator_frame = inspect.stack()[1]
        ctx = decorator_frame[0].f_locals
        first_line_number = decorator_frame[2]
    else:
        ctx = func_or_class.__globals__
        first_line_number = func_or_class.__code__.co_firstlineno

    source = inspect.getsource(func_or_class)
    tree = ast.parse(dedent(source))
    ast.increment_lineno(tree, first_line_number - 1)

    tree.body[0].decorator_list = [
        d
        for d in tree.body[0].decorator_list
        if not (isinstance(d, ast.Name) and d.id == "pyped")
    ]
    tree = PipeTransformer().visit(tree)
    ast.fix_missing_locations(tree)

    # Compile and execute
    code = compile(tree, filename=(ctx.get("__file__", "repl")), mode="exec")
    exec(code, ctx)
    return ctx[tree.body[0].name]  # type: ignore


if __name__ == "__main__":

    @pyped
    def test_function(x: int) -> int:
        return x >> str >> list >> len

    print(test_function(123))
