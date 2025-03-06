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
    Name,
    NamedExpr,
    NodeTransformer,
    Return,
    RShift,
    expr,
    keyword,
)
from ast import (
    stmt as statement,
)
from typing import Callable, final

from pypeduct.helpers import NODE, _ensure_loc


@final
class PipeTransformer(NodeTransformer):
    def __init__(self, hofs: set[Callable]) -> None:
        self.lambda_counter = 0
        self.assignment_stack: list[list[Assign]] = [[]]
        self.current_block_assignments: list[Assign] = []
        self.generator_depth = 0
        self.in_lambda = False
        self.function_params = {}  # {name: (num_pos_args, has_varargs)}
        self.hofs = hofs

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
        num_pos_args = len(node.args.posonlyargs) + len(node.args.args)
        has_varargs = node.args.vararg is not None
        self.function_params[node.name] = (num_pos_args, has_varargs)
        self.generic_visit(node)
        return node

    def visit_BinOp(self, node: BinOp) -> AST:
        if not isinstance(node.op, RShift):
            return self.generic_visit(node)

        left = self.visit(node.left)
        original_right = node.right  # Keep the original right node before visiting

        # Check if the right is a NamedExpr (walrus operator) and not in a generator
        if isinstance(original_right, NamedExpr) and self.generator_depth == 0:
            # Process the value of the NamedExpr (right.value) without visiting the NamedExpr itself
            processed_value = self.visit(original_right.value)
            target = original_right.target
            # Handle the walrus operator within the pipeline context
            return self._handle_walrus(node, left, processed_value, target)
        else:
            # Visit the right node normally
            right = self.visit(original_right)
            # Preserve bitwise shifts for constants like numbers only.
            if isinstance(original_right, ast.Constant):
                return BinOp(left=left, op=node.op, right=right)
            # Proceed to build the pipeline call
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
        """Build the pipeline call, unpacking tuples when appropriate."""
        keywords_to_add = []
        if isinstance(right, Lambda) and right.args.kwarg and original_kwargs_name:
            keywords_to_add.append(
                keyword(arg=None, value=Name(id=original_kwargs_name, ctx=Load()))
            )

        # Determine the target function's parameters
        required_pos = 0
        has_varargs = False
        func_node = right.func if isinstance(right, Call) else right

        if isinstance(func_node, Lambda):
            required_pos, has_varargs = getattr(
                func_node, "_pyped_pos_args", (0, False)
            )
        elif isinstance(func_node, Name):
            required_pos, has_varargs = self.function_params.get(
                func_node.id, (0, False)
            )

        # Check if we should unpack the tuple
        is_tuple = isinstance(left, ast.Tuple)
        should_unpack = is_tuple and (required_pos > 1 or has_varargs)

        if should_unpack:
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
        num_pos_args = len(node.args.posonlyargs) + len(node.args.args)
        has_varargs = node.args.vararg is not None
        setattr(node, "_pyped_pos_args", (num_pos_args, has_varargs))
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
