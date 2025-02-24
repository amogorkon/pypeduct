from __future__ import annotations

import ast
from builtins import ExceptionGroup
from collections.abc import Sequence
from typing import Any, Self, final


class PipeTransformError(ExceptionGroup):
    """Enhanced exception with context for pipe transformation errors."""

    def __new__(
        cls: type[Self],
        message: str,
        exceptions: Sequence[Exception],
        *,
        context: dict[str, Any] | None = None,
    ) -> Self:
        if not exceptions:
            raise ValueError("exceptions must be a non-empty sequence")
        instance = super().__new__(cls, message, exceptions)
        instance.context = context or {}
        return instance

    def __init__(
        self,
        message: str,
        exceptions: Sequence[Exception],
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message, exceptions)
        self.context = context or {}

    def __str__(self) -> str:
        context_info = f"\nContext: {self.context}" if self.context else ""
        return f"{super().__str__()}{context_info}"


@final
class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        if not isinstance(node.op, (ast.LShift, ast.RShift)):
            return node

        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(right, ast.Attribute) and not isinstance(right.value, ast.Name):
            right = ast.Call(
                func=right,
                args=[],
                keywords=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

        if not isinstance(right, ast.Call):
            new_call = ast.Call(
                func=right,
                args=[left],
                keywords=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            return ast.copy_location(new_call, node)

        insert_pos = 0 if isinstance(node.op, ast.RShift) else len(right.args)
        right.args.insert(insert_pos, left)
        return ast.copy_location(right, node)
