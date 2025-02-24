from __future__ import annotations

import ast
import inspect
from textwrap import dedent
from typing import Any, Callable, TypeVar

from pypeduct.transformer import PipeTransformer

T = TypeVar("T", bound=Callable[..., Any] | type[Any])


def pyped(func_or_class: T) -> T:
    """Decorator transforming >>/<< operators into pipeline operations."""
    if hasattr(func_or_class, "_pyped_transformed"):
        return func_or_class

    if inspect.isclass(func_or_class):
        decorator_frame = inspect.stack()[1]
        ctx = decorator_frame.frame.f_locals.copy()
        first_line_number = decorator_frame.lineno
    elif inspect.isfunction(func_or_class):
        ctx = func_or_class.__globals__.copy()
        first_line_number = func_or_class.__code__.co_firstlineno
    else:
        raise TypeError("Can only decorate functions or classes")

    source = inspect.getsource(func_or_class)
    tree = ast.parse(dedent(source))
    tree = PipeTransformer().visit(tree)

    ast.increment_lineno(tree, first_line_number - 1)

    for node in ast.walk(tree):
        match node:
            case ast.FunctionDef() | ast.ClassDef():
                node.decorator_list = [
                    d
                    for d in node.decorator_list
                    if not (isinstance(d, ast.Name) and d.id == "pyped")
                ]
    ast.fix_missing_locations(tree)
    if __debug__:
        # Define a custom unparser to handle async generator nodes
        from ast import _Precedence, _Unparser

        class PatchedUnparser(_Unparser):
            def __init__(self):
                super().__init__()
                self._precedences.update({
                    ast.Yield: _Precedence.ATOM,
                    ast.YieldFrom: _Precedence.ATOM,
                    ast.Await: _Precedence.ATOM,
                })

        def custom_unparse(node: ast.AST) -> str:
            unparser = PatchedUnparser()
            unparser.visit(node)
            return "".join(unparser._source)

        print(f"Transformed AST:\n{custom_unparse(tree)}")

    code = compile(
        tree, filename=ctx.get("__file__", "<pyped>"), mode="exec", optimize=2
    )
    exec(code, ctx)
    func_or_class._pyped_transformed = True
    return ctx[tree.body[0].name]


if __name__ == "__main__":

    @pyped
    def test_function(x: int) -> int:
        return x >> str >> list >> len

    print(test_function(123))

    @pyped
    def kwargs_function():
        def greet(name, greeting="Hello"):
            return f"{greeting}, {name}!"

        return "Alyz" >> greet(greeting="Hi")

    print(kwargs_function())

    def test_pipe_with_async_generator():
        @pyped
        async def async_generator_pipe() -> list[int]:
            async def async_gen():
                for i in range(3):
                    yield i

            result: list[int] = [i async for i in async_gen()] >> list
            return result

        result = asyncio.run(async_generator_pipe())
        assert result == [0, 1, 2]

    @pyped
    class Test:
        __slots__ = ("id",)

        def __init__(self, id: int) -> None:
            self.id = id

        def foo(self) -> int:
            return self.id >> str >> list >> len

    t = Test(123)
    print(t.foo())
