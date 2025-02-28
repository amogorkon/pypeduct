from __future__ import annotations

import ast
from ast import (
    AST,
    Assign,
    BinOp,
    Call,
    For,
    FunctionDef,
    If,
    Lambda,
    Load,
    LShift,
    Name,
    NamedExpr,
    NodeTransformer,
    Return,
    RShift,
    copy_location,
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
        self.assignment_stack: list[list[Assign]] = [[]]
        self.current_block_assignments: list[Assign] = []
        self.generator_depth = 0
        self.in_lambda = False

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        new_body: list[AST] = []
        for stmt in node.body:
            self.current_block_assignments = []
            processed = self.visit(stmt)
            new_body.extend(self.current_block_assignments)
            if isinstance(processed, list):
                new_body.extend(processed)
            else:
                new_body.append(processed)
        node.body = new_body
        return node

    def visit_BinOp(self, node: BinOp) -> AST:
        if not isinstance(node.op, (LShift, RShift)):
            return self.generic_visit(node)

        left = self.visit(node.left)
        right = self.visit(node.right)

        if isinstance(node.right, NamedExpr) and self.generator_depth == 0:
            return self._handle_walrus_step(node, left)

        return self._build_pipeline_call(node, left, right)

    def _handle_walrus_step(self, node: BinOp, left: AST) -> AST:
        target = node.right.target
        func = self.visit(node.right.value)

        call = Call(
            func=func,
            args=[left],
            keywords=[],
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        assignment = Assign(
            targets=[target], value=call, lineno=node.lineno, col_offset=node.col_offset
        )
        self.current_block_assignments.append(assignment)
        return Name(id=target.id, ctx=Load())

    def _build_pipeline_call(self, node: BinOp, left: AST, right: AST) -> AST:
        """Build the pipeline function call structure"""
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

    def visit_NamedExpr(self, node: NamedExpr) -> AST:
        if self.generator_depth > 0 or self.in_lambda:
            processed_value = self.visit(node.value)
            return copy_location(
                NamedExpr(target=node.target, value=processed_value), node
            )

        processed_value = self.visit(node.value)
        assignment = Assign(
            targets=[node.target],
            value=processed_value,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        self.current_block_assignments.append(assignment)
        return Name(id=node.target.id, ctx=Load())

    def visit_If(self, node: If) -> If:
        node.test = self.visit(node.test)

        # if-body
        original_assignments = self.current_block_assignments
        self.current_block_assignments = []
        node.body = [self.visit(stmt) for stmt in node.body]
        node.body = self.current_block_assignments + node.body

        # else-body
        self.current_block_assignments = []
        node.orelse = [self.visit(stmt) for stmt in node.orelse]
        node.orelse = self.current_block_assignments + node.orelse

        self.current_block_assignments = original_assignments
        return node

    def visit_For(self, node: For) -> For:
        node.target = self.visit(node.target)
        node.iter = self.visit(node.iter)

        original_assignments = self.current_block_assignments
        self.current_block_assignments = []
        node.body = [self.visit(stmt) for stmt in node.body]
        node.body = self.current_block_assignments + node.body
        self.current_block_assignments = original_assignments

        return node

    def _lambda_to_named_function(self, name: str, lambda_node: Lambda) -> FunctionDef:
        """Convert lambda with assignments to named function"""
        return FunctionDef(
            name=name,
            args=lambda_node.args,
            body=[*self.current_block_assignments, Return(value=lambda_node.body)],
            decorator_list=[],
            returns=None,
        )

    def _generate_lambda_name(self) -> str:
        self.lambda_counter += 1
        return f"_lambda_{self.lambda_counter}"

    def visit_GeneratorExp(self, node: ast.GeneratorExp) -> ast.GeneratorExp:
        self.generator_depth += 1
        node.elt = self.visit(node.elt)
        for gen in node.generators:
            gen.target = self.visit(gen.target)
            gen.iter = self.visit(gen.iter)
            gen.ifs = [self.visit(iff) for iff in gen.ifs]
        self.generator_depth -= 1

        return node

    def visit_Lambda(self, node: Lambda) -> AST:
        original_assignments = self.current_block_assignments
        original_in_lambda = self.in_lambda
        self.current_block_assignments = []
        self.in_lambda = True

        processed_body = self.visit(node.body)

        if self.current_block_assignments:
            new_body = [*self.current_block_assignments, Return(value=processed_body)]

            func_name = self._generate_lambda_name()
            func_def = FunctionDef(
                name=func_name,
                args=node.args,
                body=new_body,
                decorator_list=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

            self.current_block_assignments = original_assignments
            self.current_block_assignments.append(func_def)

            return copy_location(Name(id=func_name, ctx=Load()), node)

        self.current_block_assignments = original_assignments
        self.in_lambda = original_in_lambda
        return node

    def visit_Return(self, node: Return) -> list[AST]:
        original_assignments = self.current_block_assignments
        self.current_block_assignments = []
        node.value = self.visit(node.value)
        assignments = self.current_block_assignments
        self.current_block_assignments = original_assignments
        return assignments + [node]
