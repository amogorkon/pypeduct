# helpers.py

import ast
import contextlib
import inspect
from ast import AST, Attribute, Lambda, Name, stmt
from textwrap import dedent
from typing import Callable, TypeVar

NODE = (
    ast.FunctionDef
    | ast.BinOp
    | ast.Return
    | ast.Assign
    | ast.Call
    | ast.Name
    | ast.NamedExpr
    | ast.Subscript
    | ast.Starred
    | ast.Constant
    | ast.Tuple
)

T = TypeVar("T", bound=NODE)


def ensure_loc(new: T, ref: AST) -> T:
    """Copy location information from a reference node to a new node.

    Usually you would use ast.copy_location for this purpose, but we are potentially dealing with
    synthetic nodes that may not have the locations set correctly (or at all).
    """
    new.lineno = getattr(ref, "lineno", 1)
    new.end_lineno = getattr(ref, "end_lineno", new.lineno)
    new.col_offset = getattr(ref, "col_offset", 0)
    new.end_col_offset = getattr(ref, "end_col_offset", new.col_offset)
    return new


def resolve_attribute(attr_node: ast.Attribute, globals_dict: dict) -> object | None:
    """Safely resolves an attribute without using eval(), handling nested attributes.

    Avoids invoking callables (e.g., instantiating classes or calling functions)
    to prevent any side effects.
    """
    if isinstance(
        attr_node.value, ast.Constant
    ):  # Handle string literals, numbers, etc.
        base = attr_node.value.value
    elif isinstance(attr_node.value, ast.Name):  # Simple case: global lookup
        base = globals_dict.get(attr_node.value.id)
    elif isinstance(attr_node.value, ast.Attribute):  # Recursive case: obj.attr1.attr2
        base = resolve_attribute(attr_node.value, globals_dict)
    else:
        return None  # Cannot resolve function calls, indexing, etc.

    return getattr(base, attr_node.attr, None) if base is not None else None


def inject_unpack_helper(body: list[stmt]) -> list[stmt]:
    """Injects `_pyped_unpack` at the top of the transformed function.

    `_pyped_unpack` is injected directly into each transformed function to ensure:
    - The function remains **self-contained**, avoiding import and dependency issues.
    - It works even if the transformed function is copied elsewhere.
    - No pollution of the global namespace or conflicts with user-defined functions.
    - We avoid relying on static analysis of return types, ensuring correctness at runtime.

    This approach guarantees that tuple unpacking only happens when necessary, without
    requiring manual inference of return types in the AST.
    """
    unpack_source = dedent("""
    def _pyped_unpack(value, num_req: int | None, func, *args, **kwargs):
        if num_req == 1:
            return func(value, *args, **kwargs)
        if isinstance(value, tuple) and (num_req is None or len(value) >= num_req):
            return func(*value, *args, **kwargs)
        return func(value, *args, **kwargs)
    """).strip()

    # Parse from cleaned source
    unpack_ast = ast.parse(unpack_source).body[0]
    return [unpack_ast] + body


def get_num_required_args(
    func_node: AST, function_params: dict, context: dict
) -> int | None:
    if func := get_runtime_function(func_node, context):
        with contextlib.suppress(ValueError, TypeError):
            sig = inspect.signature(func)
            return sum(
                p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                and p.default is inspect.Parameter.empty
                for p in sig.parameters.values()
            )

    match func_node:
        case Lambda(args=lambda_args):
            return len(lambda_args.args)
        case Name(id=name) if name in function_params:
            return function_params[name].num_required
        case _:
            return None


def get_runtime_function(node: AST, context: dict) -> Callable | None:
    match node:
        case Name(id=name) if name in context:
            return context[name]

        case Attribute(value=ast.Constant(value=const_val), attr=attr):
            # Resolve methods on literal constants like " ".join -> str.join
            method = getattr(type(const_val), attr, None)
            if method and callable(method):
                return method.__get__(const_val)

    return None
