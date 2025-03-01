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
    expr,
    keyword,
)
from ast import (
    stmt as statement,
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
        self.function_params = {}

    def visit_FunctionDef(self, node: FunctionDef) -> FunctionDef:
        # Record the number of positional parameters for the function
        num_pos_args = len(node.args.posonlyargs) + len(node.args.args)
        self.function_params[node.name] = num_pos_args
        self.generic_visit(node)
        return node

    def visit_BinOp(self, node: BinOp) -> AST:
        if not isinstance(node.op, (LShift, RShift)):
            return self.generic_visit(node)

        left = self.visit(node.left)
        original_right = node.right

        # Handle walrus operator in pipeline
        if isinstance(original_right, NamedExpr) and self.generator_depth == 0:
            processed_value = self.visit(original_right.value)
            target = original_right.target
            return self._handle_walrus(node, left, processed_value, target)
        else:
            right = self.visit(original_right)
            if isinstance(original_right, ast.Constant):
                return BinOp(left=left, op=node.op, right=right)
            return self._build_pipeline_call(node, left, right)

    def _handle_walrus(
        self, node: BinOp, left: expr, func_call_node: expr, target: Name
    ) -> expr:
        """Handles the walrus operator within a pipeline step."""
        # Construct the function call with left as the first argument
        if isinstance(func_call_node, Call):
            call = Call(
                func=func_call_node.func,
                args=[left] + func_call_node.args,
                keywords=func_call_node.keywords,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
        else:
            # If it's not a Call, assume it's a function reference and create a call
            call = Call(
                func=func_call_node,
                args=[left],
                keywords=[],
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

        # Create the assignment to the target of the walrus operator
        assignment = Assign(
            targets=[target],
            value=call,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        self.current_block_assignments.append(assignment)
        return call

    def _handle_assignment_node(self, target, call, node):
        assignment = ast.Assign(
            targets=[target],
            value=call,
            lineno=node.lineno,
            col_offset=node.col_offset,
        )
        self.current_block_assignments.append(assignment)
        return call

    def _build_pipeline_call(
        self,
        node: BinOp,
        left: expr,
        right: expr,
        original_kwargs_name: str | None = None,
    ) -> expr:
        """Build the pipeline call, unpacking tuples for multi-param functions."""
        keywords_to_add = []
        if isinstance(right, Lambda) and right.args.kwarg and original_kwargs_name:
            keywords_to_add.append(
                keyword(arg=None, value=Name(id=original_kwargs_name, ctx=Load()))
            )

        # Determine number of positional arguments expected by the target function
        num_pos_args = 0
        if isinstance(right, Lambda):
            num_pos_args = getattr(
                right,
                "_pyped_pos_args",
                len(right.args.posonlyargs) + len(right.args.args),
            )
        elif isinstance(right, Name):
            num_pos_args = self.function_params.get(right.id, 0)

        # Prepare arguments: unpack if function expects multiple positional args
        if num_pos_args > 1:
            args = [ast.Starred(value=left, ctx=ast.Load())]
        else:
            args = [left]

        if isinstance(right, Call):
            return Call(
                func=right.func,
                args=args + right.args,
                keywords=right.keywords + keywords_to_add,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )
        else:
            return Call(
                func=right,
                args=args,
                keywords=keywords_to_add,
                lineno=node.lineno,
                col_offset=node.col_offset,
            )

    def visit_NamedExpr(self, node: NamedExpr) -> expr:
        if self.in_lambda or self.generator_depth > 0:
            # Preserve walrus operator inside lambdas/generators
            return self.generic_visit(node)

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

    def visit_Lambda(self, node: Lambda) -> expr:
        # Record the number of positional parameters for the lambda
        num_pos_args = len(node.args.posonlyargs) + len(node.args.args)
        # Lambdas are anonymous, so track via a custom attribute
        setattr(node, "_pyped_pos_args", num_pos_args)
        self.generic_visit(node)
        return node

    def visit_Return(self, node: Return) -> list[statement]:
        original_assignments = self.current_block_assignments
        self.current_block_assignments = []
        node.value = self.visit(node.value)
        assignments = self.current_block_assignments
        self.current_block_assignments = original_assignments
        return assignments + [node]

    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        new_body = []
        for stmt in node.body:
            self.current_block_assignments = []

            processed_stmt = self.visit(stmt)

            new_body.extend(self.current_block_assignments)

            if isinstance(processed_stmt, list):
                new_body.extend(processed_stmt)
            else:
                new_body.append(processed_stmt)

        node.body = new_body
        return node
