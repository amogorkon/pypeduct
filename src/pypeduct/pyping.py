import ast
import inspect
import linecache
import sys
from functools import reduce, wraps
from textwrap import dedent
from typing import Any, Callable, Type, TypeVar

from pypeduct.transformer import PipeTransformer

T = TypeVar("T", bound=Callable[..., Any] | type[Any])

DEFAULT_HOF = {"filter": filter, "map": map, "reduce": reduce}


def print_code(code, original=True):
    print(
        f"↓↓↓↓↓↓↓ Original Code ↓↓↓↓↓↓↓ \n\n{code}\n↑↑↑↑↑↑↑ End Original Code ↑↑↑↑↑↑↑"
    ) if original else print(
        f"↓↓↓↓↓↓↓ Transformed Code ↓↓↓↓↓↓↓ \n\n{code}\n↓↓↓↓↓↓↓ End Transformed Code ↓↓↓↓↓↓↓"
    )


def pyped(
    func_or_class: T | None = None,
    *,
    verbose: bool = False,
    add_hofs: dict[str, Callable] | None = None,
) -> T | Callable[[T], T]:
    """Decorator transforming the >> operator into pipeline operations."""

    def actual_decorator(obj: T) -> T:
        transformed = None
        hofs = DEFAULT_HOF | (add_hofs or {})

        @wraps(obj)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal transformed

            if transformed is None:
                if not inspect.isclass(obj):
                    transformed = _transform_function(
                        obj, verbose, hofs, obj.__globals__.copy()
                    )
                else:
                    transformed = _transform_class(
                        obj,
                        verbose,
                        hofs,
                    )

            return transformed(*args, **kwargs)

        return wrapper  # type: ignore

    return actual_decorator(func_or_class) if func_or_class else actual_decorator


def _transform_function(
    func: Callable,
    verbose: bool,
    hofs: dict[str, Callable],
    current_globals: dict[str, Any],
) -> Callable:
    """Performs the AST transformation using the original function's context."""
    try:
        source = inspect.getsource(func)
    except OSError:
        source = _retrieve_source(func)
    source = dedent(source)
    if verbose:
        print_code(source, original=True)

    tree = PipeTransformer(hofs, current_globals, verbose=verbose).visit(
        ast.parse(source)
    )

    top_level_node = tree.body[0]
    if isinstance(
        top_level_node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
    ):
        top_level_node.decorator_list = []

    ast.fix_missing_locations(tree)

    if verbose:
        print_code(ast.unparse(tree), original=False)

    ctx = func.__globals__.copy()
    closure = func.__closure__
    if closure is not None:
        free_vars = func.__code__.co_freevars
        for name, cell in zip(free_vars, closure):
            ctx[name] = cell.cell_contents

    exec(compile(tree, filename="<pyped>", mode="exec"), ctx)  # type: ignore
    return ctx[func.__name__]


def _retrieve_source(func):
    code = func.__code__
    lines = linecache.getlines(code.co_filename)

    module_ast = ast.parse("".join(lines), code.co_filename)
    target = next(
        node
        for node in ast.walk(module_ast)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == func.__name__
        and node.lineno <= code.co_firstlineno <= node.end_lineno
    )

    result = "".join(lines[target.lineno - 1 : target.end_lineno])
    return result.split(":", 1)[1]


def _transform_class(
    cls: Type[Any],
    verbose: bool,
    hofs: set[Callable],
    current_globals: dict[str, Any] = None,
) -> Type[Any]:
    """Transforms a class by applying AST transformations to its methods, including nested classes."""
    try:
        source = inspect.getsource(cls)
    except OSError as e:
        # Fallback using AST to find class boundaries
        module_name = cls.__module__
        module = sys.modules.get(module_name)

        if not module or not getattr(module, "__file__", None):
            raise OSError(f"Could not retrieve source code for {cls.__name__}") from e

        module_file = module.__file__
        lines = linecache.getlines(module_file)
        module_ast = ast.parse("".join(lines), filename=module_file)

        # Recursively search for the class node
        class_nodes = []

        class Visitor(ast.NodeVisitor):
            def visit_ClassDef(self, node):
                if node.name == cls.__name__:
                    class_nodes.append(node)
                self.generic_visit(node)

        Visitor().visit(module_ast)

        if not class_nodes:
            raise OSError(
                f"Class {cls.__name__} not found in module {module_name}"
            ) from e

        class_node = class_nodes[0]
        start_line = class_node.lineno - 1  # 0-based
        end_line = class_node.end_lineno
        source = "".join(lines[start_line:end_line])

    source = dedent(source)

    if verbose:
        print_code(source, original=True)

    tree = ast.parse(source)
    transformer = PipeTransformer(hofs, verbose=verbose)
    transformed_tree = transformer.visit(tree)

    top_level_node = transformed_tree.body[0]
    if isinstance(top_level_node, ast.ClassDef):
        top_level_node.decorator_list = []
    ast.fix_missing_locations(transformed_tree)

    if verbose:
        print_code(ast.unparse(tree), original=False)

    if caller_frame := inspect.currentframe():
        caller_frame = caller_frame.f_back.f_back
        caller_globals = caller_frame.f_globals if caller_frame else {}
        caller_locals = caller_frame.f_locals if caller_frame else {}
    else:
        caller_globals = {}
        caller_locals = {}

    exec_globals = {**caller_globals, **caller_locals}
    exec_locals = {}

    exec(
        compile(transformed_tree, filename="<pyped>", mode="exec"),
        exec_globals,
        exec_locals,
    )

    return exec_locals[cls.__name__]
