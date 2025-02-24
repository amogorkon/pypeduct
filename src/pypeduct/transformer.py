from __future__ import annotations

import ast
from builtins import ExceptionGroup
from collections import deque
from collections.abc import Sequence
from threading import Lock
from types import MappingProxyType
from typing import Any, Deque, final, override


class PipeTransformError(ExceptionGroup):
    """Enhanced exception with context for pipe transformation errors."""

    def __new__(
        cls,
        message: str,
        exceptions: Sequence[Exception],
        *,
        context: dict[str, Any] | None = None,
    ) -> PipeTransformError:
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
    _temp_counter: int = 0
    _counter_lock: Lock = Lock()

    def __init__(self) -> None:
        super().__init__()
        self._temp_map: dict[str, ast.AST] = {}
        self._assignments: Deque[tuple[ast.AST, ast.Assign, ast.AST | None]] = deque()
        self._async_context: bool = False
        self._current_function: ast.FunctionDef | None = None
        self._parent_stack: list[ast.AST] = []

    def visit(self, node: ast.AST) -> ast.AST:
        self._parent_stack.append(node)
        try:
            return super().visit(node)
        finally:
            self._parent_stack.pop()

    @override
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:
        self._async_context = True
        node = self.generic_visit(node)
        self._async_context = False
        return node

    @override
    def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
        self._current_function = node
        original_body_length = len(node.body)

        try:
            node = self.generic_visit(node)
            self._insert_assignments(node)

            if len(node.body) < original_body_length:
                raise PipeTransformError(
                    "Function body corrupted during transformation",
                    exceptions=(ValueError("Body length mismatch"),),
                    context={
                        "function": node.name,
                        "original_length": original_body_length,
                        "new_length": len(node.body),
                    },
                )
            ast.fix_missing_locations(node)

            return node
        finally:
            self._current_function = None

    @override
    def visit_BinOp(self, node: ast.BinOp) -> Any:
        if isinstance(node.op, (ast.LShift, ast.RShift)):
            try:
                transformed = self._transform_pipe(node, node.left, node.right, node.op)
                return self._wrap_async(transformed)
            except PipeTransformError:
                raise
            except Exception as e:
                raise PipeTransformError(
                    "Unexpected transformation error",
                    exceptions=(e,),
                    context={
                        "lineno": node.lineno,
                        "col_offset": node.col_offset,
                        "code": ast.unparse(node),
                    },
                ) from e
        return self.generic_visit(node)

    def _transform_pipe(
        self, node: ast.BinOp, left: ast.AST, right: ast.AST, op: ast.operator
    ) -> ast.AST:
        left = self.visit(left)
        right = self.visit(right)

        if isinstance(right, ast.Call):
            return self._create_temp_assignment_call(node, left, right, op)
        return self._create_direct_call(node, left, right, op)

    def _create_direct_call(
        self, node: ast.BinOp, left: ast.AST, right: ast.AST, op: ast.operator
    ) -> ast.AST:
        """Handle simple case without temp variable"""
        new_call = ast.Call(
            func=right,
            args=[left],
            keywords=[],
        )
        ast.copy_location(new_call, node)
        return new_call

    def _create_temp_assignment_call(
        self, node: ast.BinOp, left: ast.AST, right: ast.Call, op: ast.operator
    ) -> ast.Call:
        temp_var = self._create_temp_assignment(left, node)
        prepend = isinstance(op, ast.RShift)

        if prepend:
            right.args.insert(0, temp_var)
        else:
            right.args.append(temp_var)

        return right

    def _create_temp_assignment(self, left: ast.AST, origin: ast.AST) -> ast.Name:
        with self._counter_lock:
            temp_id = f"__pipe_tmp_{PipeTransformer._temp_counter}"
            PipeTransformer._temp_counter += 1

        temp_name = ast.Name(id=temp_id, ctx=ast.Load())
        ast.copy_location(temp_name, origin)

        assignment = ast.Assign(
            targets=[ast.Name(id=temp_id, ctx=ast.Store())],
            value=left,
        )
        ast.copy_location(assignment, left)

        parent = self._parent_stack[-2] if len(self._parent_stack) >= 2 else None
        self._assignments.append((origin, assignment, parent))
        self._temp_map[temp_id] = left

        return temp_name

    def _insert_assignments(self, node: ast.FunctionDef) -> None:
        try:
            body = node.body
            assignments = list(self._assignments)
            self._assignments.clear()

            for origin_node, assignment, parent in assignments:
                inserted = False

                # Check if parent is a Return statement and find its position
                if isinstance(parent, ast.Return):
                    for i, body_node in enumerate(body):
                        if body_node is parent:
                            body.insert(i, assignment)
                            inserted = True
                            break
                else:
                    # Fallback: search for origin node or its expression
                    for i, body_node in enumerate(body):
                        if body_node is origin_node or (
                            isinstance(body_node, ast.Expr)
                            and body_node.value is origin_node
                        ):
                            body.insert(i, assignment)
                            inserted = True
                            break

                if not inserted:
                    # Insert at the beginning if not found
                    body.insert(0, assignment)
        except Exception as e:
            raise PipeTransformError(
                "An error occurred during pipe transformation",
                exceptions=[e],
                context={"function": node.name},
            ) from e
        finally:
            self._assignments.clear()

    def _wrap_async(self, node: ast.AST) -> ast.AST:
        return ast.Await(value=node) if self._async_context else node

    @property
    def temporary_variables(self) -> MappingProxyType[str, ast.AST]:
        return MappingProxyType(self._temp_map)
