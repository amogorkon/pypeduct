# transformer.py
import ast
from typing import Any


class PipeTransformError(Exception):
    """Custom exception for pipe transformation errors."""


class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node: ast.BinOp) -> Any:
        match node:
            case ast.BinOp(left=left, op=ast.LShift() | ast.RShift(), right=right):
                if not isinstance(right, ast.Call):
                    new_call = ast.Call(
                        func=right,
                        args=[left],
                        keywords=[],
                        lineno=right.lineno,
                        col_offset=right.col_offset,
                    )
                    return self.visit(new_call)
                else:
                    if (
                        not isinstance(left, ast.Call)
                        and not isinstance(left, ast.Name)
                        and not isinstance(left, ast.Constant)
                    ):
                        raise PipeTransformError(
                            "Left-hand side of pipe must be a callable or variable."
                        )
                    insert_position = (
                        0 if isinstance(node.op, ast.RShift) else len(right.args)
                    )
                    right.args.insert(insert_position, left)
                    return self.visit(right)
            case _:
                return self.generic_visit(node)
