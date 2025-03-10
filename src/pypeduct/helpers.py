import ast
import contextlib
import inspect
from ast import AST, Attribute, Lambda, Name, parse, stmt
from collections.abc import Sequence
from typing import Callable, Protocol, TypeVar, get_origin, runtime_checkable

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


def is_seq_ast(annotation: ast.AST) -> bool:
    """

    Determines if an annotation should be unpacked based on its type.
    Returns True for list, tuple, or Sequence types; False for str and bytes.
    """
    # If annotation is a simple name (e.g. list, tuple, Sequence)
    if isinstance(annotation, ast.Name):
        if annotation.id in {"list", "tuple", "Sequence", "List", "Tuple"}:
            return True
        if annotation.id in {"str", "bytes"}:
            return False


@runtime_checkable
class SequenceProtocol(Protocol):
    def __getitem__(self, index: int) -> object: ...
    def __len__(self) -> int: ...


def is_seq_runtime(annotation: type | None) -> bool:
    """Returns True if annotation represents a sequence type (except str/bytes).

    - Extracts the origin of generic types (e.g., list[int], Sequence[str]) for proper type checking.
    - Ensures `None` values and non-types do not raise errors.
    - Excludes `str` and `bytes`, which are technically sequences but should not be unpacked.
    - Handles `tuple[()]` edge cases gracefully.
    - Recognizes user-defined (duck-typed) sequence types if they conform to the SequenceProtocol.
    """
    if annotation is None:
        return False

    origin = get_origin(annotation)
    if origin is not None:
        annotation = origin

    if not isinstance(annotation, type):
        return False

    return (
        issubclass(annotation, Sequence) or issubclass(annotation, SequenceProtocol)
    ) and annotation not in (str, bytes, tuple[()])


def should_unpack(annotation: ast.AST) -> bool:
    """Determines if an annotation should be unpacked based on its type."""
    if is_seq_ast(annotation):
        return True
    if isinstance(annotation, ast.Subscript):
        return is_seq_runtime(annotation.value)
    return False


def is_single_arg_func(func_node: AST, current_globals: dict) -> bool:
    """Check if function expects exactly 1 positional argument."""
    try:
        if isinstance(func_node, Name):
            if func := current_globals.get(func_node.id):
                with contextlib.suppress(ValueError):
                    sig = inspect.signature(func)
                    params = list(sig.parameters.values())
                    num_required = sum(
                        p.default is inspect.Parameter.empty
                        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                        for p in params
                    )
                    return num_required == 1

        elif isinstance(func_node, Attribute):
            func = resolve_attribute(func_node, current_globals)
            if not func:
                return False

            with contextlib.suppress(ValueError):
                sig = inspect.signature(func)
                params = list(sig.parameters.values())
                num_required = sum(
                    p.default is inspect.Parameter.empty
                    and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                    for p in params
                )
                return num_required == 1

    except Exception:
        pass

    return False


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
    unpack_function = parse("""
def _pyped_unpack(value, num_args: int, func):
    '''Helper function to unpack a tuple if necessary, injected into the AST by inject_unpack_helper.'''
    if num_args > 1 and isinstance(value, tuple):
        return func(*value)
    return func(value)
        """).body[0]  # Extract the function AST node

    return [unpack_function] + body  # Insert at the top


def _get_num_positional_params(
    func_node: AST, function_params: dict, current_globals: dict
) -> int | None:
    # Check locally defined functions first
    if isinstance(func_node, Name) and func_node.id in function_params:
        return function_params[func_node.id].num_pos

    # Check global functions
    if func := get_runtime_function(func_node, current_globals=current_globals):
        with contextlib.suppress(ValueError):
            sig = inspect.signature(func)
            return len([
                p
                for p in sig.parameters.values()
                if p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
            ])
    return None  # Unknown arity


def get_runtime_function(node: AST, current_globals: dict) -> Callable | None:
    match node:
        case Name(id=name) if name in current_globals:
            return current_globals[name]

        case Attribute(value=ast.Constant(value=const_val), attr=attr):
            # Resolve methods on literal constants like " ".join -> str.join
            method = getattr(type(const_val), attr, None)
            if method and callable(method):
                return method.__get__(const_val)

    return None


def _has_sequence_annotation(
    func_node: AST, function_params: dict, current_globals: dict
) -> bool:
    """Check if first parameter expects a sequence using AST and runtime info."""
    # Local functions (defined in decorated scope)
    if isinstance(func_node, Name) and func_node.id in function_params:
        func_info = function_params[func_node.id]
        if not func_info.param_annotations:
            return False
        ann = func_info.param_annotations[0]
        return is_seq_ast(ann) or is_seq_runtime(ann)

    # Lambdas
    if isinstance(func_node, Lambda) and func_node.args.args:
        ann = func_node.args.args[0].annotation
        return is_seq_ast(ann) or is_seq_runtime(ann)

    # External functions (using resolve_attribute)
    if isinstance(func_node, (Name, Attribute)):
        func_obj = None
        if isinstance(func_node, Name):
            func_obj = current_globals.get(func_node.id)
        elif isinstance(func_node, Attribute):
            func_obj = resolve_attribute(func_node, current_globals)

        if func_obj and hasattr(func_obj, "__annotations__"):
            params = list(inspect.signature(func_obj).parameters.values())
            # Skip self/cls for bound methods
            offset = 1 if hasattr(func_obj, "__self__") else 0
            if params[offset:]:
                ann_type = func_obj.__annotations__.get(params[offset].name)
                return is_seq_runtime(ann_type)

    return False


def get_required_params(func: object) -> int:
    sig = inspect.signature(func)
    params = list(sig.parameters.values())
    # Check if it is a bound method (e.g., " ".join)
    if getattr(func, "__self__", None) is not None and params:
        # Remove 'self' from the count.
        params = params[1:]
    return sum(
        1
        for p in params
        if p.default is inspect.Parameter.empty
        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
    )


def _is_single_arg_func(func_node: AST, current_globals: dict) -> bool:
    """Check if function expects exactly 1 positional argument."""
    try:
        if isinstance(func_node, Name):
            if func_obj := current_globals.get(func_node.id):
                with contextlib.suppress(ValueError):
                    sig = inspect.signature(func_obj)
                    params = list(sig.parameters.values())
                    num_required = sum(
                        p.default is inspect.Parameter.empty
                        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                        for p in params
                    )
                    return num_required == 1

        elif isinstance(func_node, Attribute):
            func = resolve_attribute(func_node, current_globals)
            if not func:
                return False

            with contextlib.suppress(ValueError):
                sig = inspect.signature(func)
                params = list(sig.parameters.values())
                num_required = sum(
                    p.default is inspect.Parameter.empty
                    and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                    for p in params
                )
                return num_required == 1

    except Exception:
        pass

    return False


def _should_unpack(func_node: AST, left: ast.expr, current_globals: dict) -> bool:
    """Decides if `left` should be unpacked when passed to `func_node`."""
    if isinstance(left, ast.Constant) and isinstance(
        left.value, (str, bytes, int, float)
    ):
        return False

    return (
        False
        if _is_single_arg_func(func_node, current_globals=current_globals)
        else isinstance(left, ast.Tuple)
    )


def _has_varargs(func_node: AST, function_params: dict) -> bool:
    match func_node:
        case Name(id=name) if name in function_params:
            return function_params[name].has_varargs
        case Lambda(args=lambda_args):
            return lambda_args.vararg is not None
    return False


def _expected_positional_args(func_node: AST, function_params: dict) -> int:
    match func_node:
        case Name(id=name) if name in function_params:
            return function_params[name].num_pos
        case Lambda(args=lambda_args):
            return len(lambda_args.posonlyargs) + len(lambda_args.args)
    return 1
