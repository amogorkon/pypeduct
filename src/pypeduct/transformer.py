from __future__ import annotations

from ast import (
    AST,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    Call,
    FunctionDef,
    Load,
    LShift,
    Name,
    NamedExpr,
    NodeTransformer,
    RShift,
    Store,
    copy_location,
    stmt,
)
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
class PipeTransformer(NodeTransformer):
    def __init__(self) -> None:
        self.parent_stack: list[AST] = []
        self.current_stmt: stmt | None = None
        self.current_assignments: list[Assign] = []  # Track assignments per statement

    def visit(self, node: AST) -> AST:
        self.parent_stack.append(node)
        try:
            return super().visit(node)
        finally:
            self.parent_stack.pop()

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        new_body = []
        for stmt in node.body:
            self.current_stmt = stmt
            self.current_assignments = []  # Reset for each statement
            new_stmt = self.visit(stmt)
            # Prepend collected assignments to the new body
            new_body.extend(self.current_assignments)
            if isinstance(new_stmt, list):
                new_body.extend(new_stmt)
            else:
                new_body.append(new_stmt)
        self.current_stmt = None
        node.body = new_body
        return node

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> AsyncFunctionDef:
        new_body = []
        for stmt in node.body:
            self.current_stmt = stmt
            self.current_assignments = []  # Reset for each statement
            new_stmt = self.visit(stmt)
            new_body.extend(self.current_assignments)
            if isinstance(new_stmt, list):
                new_body.extend(new_stmt)
            else:
                new_body.append(new_stmt)
        self.current_stmt = None
        node.body = new_body
        return node

    def visit_BinOp(self, node: BinOp) -> AST:
        if not isinstance(node.op, (LShift, RShift)):
            return node

        if isinstance(node.left, NamedExpr):
            return self._transform_walrus_pipeline(node)
        return self._transform_regular_pipeline(node)

    def _transform_walrus_pipeline(self, node: BinOp) -> AST:
        target = node.left.target
        value = node.left.value
        if hasattr(target, "ctx"):
            target.ctx = Store()

        assign = copy_location(Assign(targets=[target], value=self.visit(value)), node)

        # Convert target to Load context for pipeline
        if isinstance(target, Name):
            target_load = copy_location(Name(id=target.id, ctx=Load()), target)
        elif isinstance(target, Attribute):
            target_load = copy_location(
                Attribute(value=target.value, attr=target.attr, ctx=Load()),
                target,
            )
        else:
            target_load = target
            if hasattr(target_load, "ctx"):
                target_load.ctx = Load()

        # Collect the assignment instead of inserting into function body
        self.current_assignments.append(assign)

        new_node = copy_location(
            BinOp(
                left=target_load,
                op=node.op,
                right=node.right,
            ),
            node,
        )
        return self.visit(new_node)

    def _transform_regular_pipeline(self, node: BinOp) -> AST:
        left = self.visit(node.left)
        right = self.visit(node.right)

        if not isinstance(right, Call):
            right = Call(
                func=right,
                args=[],
                keywords=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

        insert_pos = 0 if isinstance(node.op, RShift) else len(right.args)
        right.args.insert(insert_pos, left)
        return right
