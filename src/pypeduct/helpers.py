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


def _ensure_loc[T: NODE](new: T, ref: AST) -> T:
    new.lineno = getattr(ref, "lineno", 1)
    new.end_lineno = getattr(ref, "end_lineno", new.lineno)
    new.col_offset = getattr(ref, "col_offset", 0)
    new.end_col_offset = getattr(ref, "end_col_offset", new.col_offset)
    return new


def _requires_unpack(left: ast.expr, annotation: AST | None) -> bool:
    return isinstance(left, ast.Tuple) and not _is_sequence_annotation(annotation)
