from __future__ import annotations

from ast import (
    AST,
    Assign,
    AsyncFunctionDef,
    BinOp,
    Call,
    FunctionDef,
    Lambda,
    Load,
    LShift,
    Name,
    NamedExpr,
    NodeTransformer,
    RShift,
    Store,
    arguments,
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
        self.current_assignments: list[Assign] = []

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        node.body = self._transform_body(node.body)
        return node

    def visit_AsyncFunctionDef(self, node: AsyncFunctionDef) -> AsyncFunctionDef:
        node.body = self._transform_body(node.body)
        return node

    def _transform_body(self, body: list[stmt]) -> list[stmt]:
        new_body: list[stmt] = []
        for statement in body:
            self.current_assignments = []
            transformed_stmt: stmt = self.visit(statement)
            assert isinstance(transformed_stmt, (stmt, list))
            new_body.extend(self.current_assignments)
            if isinstance(transformed_stmt, list):
                new_body.extend(transformed_stmt)
            else:
                new_body.append(transformed_stmt)
        return new_body

    def visit_BinOp(self, node: BinOp) -> AST:
        if not isinstance(node.op, (LShift, RShift)):
            return self.generic_visit(node)

        right = node.right  # Visit right first in case it has named expressions
        if isinstance(node.right, NamedExpr):
            right_target = node.right.target
            right_value = self.visit(node.right.value)

            if hasattr(right_target, "ctx"):
                right_target.ctx = Store()

            assign_func = Assign(targets=[right_target], value=right_value)
            self.current_assignments.append(assign_func)
            right_func_name = Name(id=right_target.id, ctx=Load())
        else:
            right_func_name = self.visit(right)

        left = self.visit(node.left)

        if isinstance(node.right, NamedExpr):
            call = Call(
                func=right_func_name,
                args=[left],
                keywords=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
            assign_result = Assign(targets=[right_target], value=call)
            self.current_assignments.append(assign_result)
            return Name(id=right_target.id, ctx=Load())
        else:
            return self._transform_regular_pipeline(node, left, right_func_name)

    def _handle_named_expr(self, named_expr: NamedExpr) -> Name:
        target = named_expr.target
        value = self.visit(named_expr.value)

        if isinstance(value, Lambda):
            function_name = f"_lambda_{target.id}"
            args = arguments(
                posonlyargs=[],
                args=value.args.args,
                kwonlyargs=value.args.kwonlyargs,
                kw_defaults=value.args.kw_defaults,
                defaults=value.args.defaults,
                vararg=value.args.vararg,
                kwarg=value.args.kwarg,
            )
            function_def = FunctionDef(
                name=function_name,
                args=args,
                body=value.body if isinstance(value.body, list) else [value.body],
                decorator_list=[],
                returns=None,
            )
            self.current_assignments.append(function_def)
            callable_name = Name(id=function_name, ctx=Load())
            assign_value = Call(func=callable_name, args=[], keywords=[])
        else:
            assign_value = value

        if hasattr(target, "ctx"):
            target.ctx = Store()

        assign = Assign(targets=[target], value=assign_value)
        self.current_assignments.append(assign)

        return Name(id=target.id, ctx=Load())

    def _transform_regular_pipeline(self, node: BinOp, left, right) -> AST:
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
