# pyping.py

import ast
import builtins
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
        f"↓↓↓↓↓↓↓ Transformed Code ↓↓↓↓↓↓↓ \n\n{code}\n↑↑↑↑↑↑↑ End Transformed Code ↑↑↑↑↑↑↑"
    )


def pyped(
    func_or_class: T | None = None,
    *,
    verbose: bool = False,
    add_hofs: dict[str, Callable] | None = None,
) -> T | Callable[[T], T]:
    """Decorator transforming the >> operator into pipeline operations."""

    def actual_decorator(obj: T) -> T:
        hofs = DEFAULT_HOF | (add_hofs or {})

        if inspect.isclass(obj):
            module = sys.modules.get(obj.__module__)
            current_globals = module.__dict__ if module else {}
            return _transform_class(obj, verbose, hofs, current_globals)

        transformed = None

        @wraps(obj)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            nonlocal transformed

            if transformed is None:
                caller_frame = sys._getframe(1)
                context = {
                    **builtins.__dict__,
                    **caller_frame.f_globals,
                    **caller_frame.f_locals,
                }
                if verbose:
                    print("#### Current Context Builtins ####")
                    print(*builtins.__dict__.keys(), sep=", ")
                    print("#### Current Context Globals ####")
                    print(*caller_frame.f_globals.keys(), sep=", ")
                    print("#### Current Context Locals ####")
                    print(*caller_frame.f_locals.keys(), sep=", ")

                transformed = _transform_function(obj, verbose, hofs, context)

            return transformed(*args, **kwargs)

        return wrapper  # type: ignore

    return actual_decorator(func_or_class) if func_or_class else actual_decorator


def _transform_function(
    func: Callable,
    verbose: bool,
    hofs: dict[str, Callable],
    context: dict[str, Any],
) -> Callable:
    """Performs the AST transformation using the original function's context."""
    if func.__closure__:
        free_vars = func.__code__.co_freevars
        closure_vars = {
            name: cell.cell_contents for name, cell in zip(free_vars, func.__closure__)
        }
        context |= closure_vars | {"__closure__": func.__closure__}
        if verbose:
            print("#### Closure Variables ####")
            print(*closure_vars.keys(), sep=", ")

    try:
        source = inspect.getsource(func)
    except OSError:
        source = _retrieve_function_source(func)
    source = dedent(source)
    if verbose:
        print_code(source, original=True)

    tree = ast.parse(source)

    if func.__defaults__:
        top_level_node = tree.body[0]
        if isinstance(top_level_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            new_defaults = []
            for default in func.__defaults__:
                try:
                    default_repr = repr(default)
                    parsed_node = ast.parse(default_repr, mode="eval").body
                    new_defaults.append(parsed_node)
                except SyntaxError:
                    original_index = len(new_defaults)
                    original_node = top_level_node.args.defaults[original_index]
                    new_defaults.append(original_node)
            top_level_node.args.defaults = new_defaults

    tree = PipeTransformer(hofs, context, verbose=verbose).visit(tree)

    top_level_node = tree.body[0]
    if isinstance(
        top_level_node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)
    ):
        top_level_node.decorator_list = []

    ast.fix_missing_locations(tree)

    if verbose:
        print_code(ast.unparse(tree), original=False)

    if closure := func.__closure__:
        free_vars = func.__code__.co_freevars
        for name, cell in zip(free_vars, closure):
            context[name] = cell.cell_contents

    exec(compile(tree, filename="<pyped>", mode="exec"), context)  # type: ignore

    new_func = context[func.__name__]

    if func.__defaults__ is not None:
        new_func.__defaults__ = func.__defaults__
    if func.__kwdefaults__ is not None:
        new_func.__kwdefaults__ = func.__kwdefaults__

    return new_func


def _retrieve_function_source(func: Callable) -> str:
    """Retrieves source code for functions where inspect.getsource fails."""
    code = func.__code__
    lines = linecache.getlines(code.co_filename)

    # Find the correct AST node
    module_ast = ast.parse("".join(lines), code.co_filename)
    for node in ast.walk(module_ast):
        if (
            isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == func.__name__
            and node.lineno <= code.co_firstlineno <= node.end_lineno
        ):
            return "".join(lines[node.lineno - 1 : node.end_lineno])

    raise OSError(f"Could not retrieve source for {func.__name__}")


def _transform_class(
    cls: Type[Any],
    verbose: bool,
    hofs: dict[str, Callable],
    context: dict[str, Any],
) -> Type[Any]:
    """Transforms a class by applying AST transformations to its methods and nested classes."""
    try:
        source = inspect.getsource(cls)
    except OSError as e:
        source = _retrieve_class_source(cls, e)

    source = dedent(source)
    if verbose:
        print_code(source, original=True)

    tree = ast.parse(source)
    transformer = PipeTransformer(hofs, context, verbose)
    transformed_tree = transformer.visit(tree)

    # Remove @pyped decorator while preserving others
    class_node = transformed_tree.body[0]
    if isinstance(class_node, ast.ClassDef):
        class_node.decorator_list = [
            dec for dec in class_node.decorator_list if not is_pyped_decorator(dec)
        ]

    ast.fix_missing_locations(transformed_tree)

    if verbose:
        print_code(ast.unparse(transformed_tree), original=False)

    exec_globals = get_full_exec_context(cls, context)
    exec(compile(transformed_tree, filename="<pyped>", mode="exec"), exec_globals)
    return exec_globals[cls.__name__]


def _retrieve_class_source(cls: Type[Any], original_error: Exception) -> str:
    """Retrieves class source code from module file."""
    module = sys.modules.get(cls.__module__)
    if not module or not getattr(module, "__file__", None):
        raise OSError(
            f"Could not retrieve source code for {cls.__name__}"
        ) from original_error

    lines = linecache.getlines(module.__file__)
    class_node = _find_class_ast_node(module.__file__, lines, cls.__name__)
    return "".join(lines[class_node.lineno - 1 : class_node.end_lineno])


def is_pyped_decorator(node: ast.expr) -> bool:
    """Identifies @pyped decorator in AST nodes."""
    match node:
        case ast.Name(id="pyped"):
            return True
        case ast.Call(func=ast.Name(id="pyped")):
            return True
    return False


def _find_class_ast_node(
    filename: str, lines: list[str], class_name: str
) -> ast.ClassDef:
    module_ast = ast.parse("".join(lines), filename)
    if class_nodes := [
        node
        for node in ast.walk(module_ast)
        if isinstance(node, ast.ClassDef) and node.name == class_name
    ]:
        return (
            max(
                class_nodes,
                key=lambda n: n.lineno,  # Pick last definition
            )
            if len(class_nodes) > 1
            else class_nodes[0]
        )
    else:
        raise OSError(f"Class {class_name} not found in module {filename}")


def get_full_exec_context(cls, current_globals: dict[str, Any]) -> dict[str, Any]:
    """
    Traverses the entire call stack to accumulate a union of all globals and locals,
    ensuring that any decorator (or other local dependency) is present.

    This is extremely costly (factor 1000).
    If this is only done once on startup it may be acceptable, but we need to make sure this is the case.
    """
    module = sys.modules.get(cls.__module__)
    context = {**(module.__dict__ if module else {}), **current_globals}
    for frame_info in inspect.stack():
        context |= frame_info.frame.f_globals | frame_info.frame.f_locals
    return context
