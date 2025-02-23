# piping.py
from __future__ import annotations

import ast
import inspect
from textwrap import dedent
from typing import Any, Callable, TypeVar, Union

from pypeduct.transformer import PipeTransformer, PipeTransformError

T = TypeVar("T", bound=Union[Callable[..., Any], type])


def pyped(func_or_class: T) -> T:
    try:
        if inspect.isclass(func_or_class):
            decorator_frame = inspect.stack()[1]
            ctx = decorator_frame.frame.f_locals
            first_line_number = decorator_frame.lineno
        else:
            ctx = func_or_class.__globals__
            first_line_number = func_or_class.__code__.co_firstlineno

        source = inspect.getsource(func_or_class)
        tree = ast.parse(dedent(source))
        ast.increment_lineno(tree, first_line_number - 1)

        def is_pyped_decorator(node: ast.AST) -> bool:
            match node:
                case ast.Name(id="pyped"):
                    return True
                case ast.Call(func=ast.Name(id="pyped")):
                    return True
                case _:
                    return False

        tree.body[0].decorator_list = [
            d for d in tree.body[0].decorator_list if not is_pyped_decorator(d)
        ]

        transformer = PipeTransformer()
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)

        code = compile(tree, filename=ctx.get("__file__", "<string>"), mode="exec")
        exec(code, ctx)
        return ctx[tree.body[0].name]
    except (AttributeError, SyntaxError, TypeError) as e:  # Specific exception handling
        raise PipeTransformError(f"Failed to transform: {e}") from e


if __name__ == "__main__":

    @pyped
    def test_function(x: int) -> int:
        return x >> str >> list >> len

    print(test_function(123))
