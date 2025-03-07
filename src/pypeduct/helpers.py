import ast
from ast import AST, Name, Subscript
from typing import TypeVar

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


def _is_sequence_annotation(annot: AST | None) -> bool:
    match annot:
        case Name(id=("list" | "tuple" | "Sequence")):
            return True
        case Subscript(value=Name(id=("list" | "tuple" | "Sequence"))):
            return True
        case _:
            return False


def ensure_loc[T: NODE](new: T, ref: AST) -> T:
    new.lineno = getattr(ref, "lineno", 1)
    new.end_lineno = getattr(ref, "end_lineno", new.lineno)
    new.col_offset = getattr(ref, "col_offset", 0)
    new.end_col_offset = getattr(ref, "end_col_offset", new.col_offset)
    return new


def should_unpack(annotation: ast.AST) -> bool:
    """
    Examine an AST node representing an annotation and decide if
    the piped value should be unpacked (via a Starred node) based on it.

    Returns True if the annotation indicates a type that is a Sequence
    (e.g. list, tuple, or Sequence) and is not one of the types (str, bytes)
    that should not be unpacked.
    """
    # If annotation is a simple name (e.g. list, tuple, Sequence)
    if isinstance(annotation, ast.Name):
        if annotation.id in {"list", "tuple", "Sequence", "List", "Tuple"}:
            return True
        if annotation.id in {"str", "bytes"}:
            return False

    # If annotation is subscripted (like list[int] or tuple[int, ...]),
    # inspect the underlying type.
    if isinstance(annotation, ast.Subscript):
        return should_unpack(annotation.value)

    # If annotation is an attribute (like typing.Sequence or collections.abc.Sequence),
    # check the attribute name.
    if isinstance(annotation, ast.Attribute) and annotation.attr in {
        "Sequence",
        "List",
        "Tuple",
    }:
        return True

    return True
