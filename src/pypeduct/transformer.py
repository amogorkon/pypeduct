from __future__ import annotations

from ast import (
    AST,
    Assign,
    BinOp,
    Call,
    FunctionDef,
    Lambda,
    Load,
    LShift,
    Name,
    NamedExpr,
    NodeTransformer,
    Return,
    RShift,
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
        self.lambda_counter = 0
        self.current_assignments: list[Assign] = []

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        new_body: Sequence[Assign | AST] = []
        for stmt in node.body:
            self.current_assignments = []
            processed_stmt = self.generic_visit(stmt)
            new_body.extend(self.current_assignments)
            new_body.append(processed_stmt)
        self.current_assignments = []
        node.body = new_body
        return node

    def _generate_lambda_name(self) -> str:
        self.lambda_counter += 1
        return f"_lambda_{self.lambda_counter}"

    def visit_BinOp(self, node: BinOp) -> AST:
        if not isinstance(node.op, (LShift, RShift)):
            return self.generic_visit(node)

        right = self.visit(node.right)
        left = self.visit(node.left)

        if isinstance(node.right, NamedExpr):
            return self._construct_function_call(node, left)
        return self._build_pipeline_call(node, left, right)

    def _construct_function_call(self, node, left):
        right_target = node.right.target
        named_expr_value = node.right.value

        func_to_call: AST = None

        if isinstance(named_expr_value, Lambda):
            lambda_name = self._generate_lambda_name()
            func_def = self._lambda_to_named_function(lambda_name, named_expr_value)
            self.current_assignments.append(func_def)
            func_to_call = Name(id=lambda_name, ctx=Load())

        if func_to_call is None:
            func_to_call = self.visit(named_expr_value)

        call = Call(
            func=func_to_call,
            args=[left],
            keywords=[],
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

        result_assign = Assign(
            targets=[right_target],
            value=call,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        self.current_assignments.append(result_assign)

        return Name(id=right_target.id, ctx=Load())

    def _lambda_to_named_function(self, name: str, lambda_node: Lambda) -> FunctionDef:
        """Convert lambda to a named function definition."""
        return FunctionDef(
            name=name,
            args=lambda_node.args,
            body=[Return(value=self.visit(lambda_node.body))],
            decorator_list=[],
            returns=None,
        )

    def _build_pipeline_call(self, node: BinOp, left: AST, right: AST) -> AST:
        """Build pipeline call, merging left value into existing call arguments if needed"""
        if isinstance(right, Call):
            return Call(
                func=right.func,
                args=[left] + right.args,
                keywords=right.keywords,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
        return Call(
            func=right,
            args=[left],
            keywords=[],
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
