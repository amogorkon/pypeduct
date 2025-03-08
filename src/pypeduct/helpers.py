import ast
from ast import AST, Attribute, Name
from collections.abc import Sequence
import inspect
from typing import Protocol, TypeVar, get_origin, runtime_checkable

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


def ensure_loc[T: NODE](new: T, ref: AST) -> T:
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


def is_seq_runtime(annotation) -> bool:
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


def is_single_arg_func(func_node: AST, current_globals) -> bool:
    """Check if function expects exactly 1 positional argument."""
    try:
        if isinstance(func_node, Name):
            if func := current_globals.get(func_node.id):
                try:
                    sig = inspect.signature(func)
                except ValueError:
                    # Built-in without signature - assume multi-arg
                    return False
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

            try:
                sig = inspect.signature(func)
            except ValueError:
                # Built-in without signature - assume multi-arg
                return False

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
