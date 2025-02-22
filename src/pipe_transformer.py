from __future__ import annotations

import ast
import inspect
import sys
import uuid
import types
from collections.abc import Callable


class PipeTransformError(Exception):
    """Exception raised for errors during pipe transformation."""

    def add_note(self, note: str) -> None:
        return super().add_note(note)  # Python 3.11+ feature


class PipeTransformer(ast.NodeTransformer):
    def __init__(self):
        self.temp_registry: dict[str, ast.stmt] = {}
        self.scope_stack: list[set[str]] = [set()]
        self.closure_cells: dict[int, list[types.CellType]] = {}
        self.current_closure: int | None = None

    def visit_Module(self, node: ast.Module) -> ast.Module:
        self.scope_stack.append(set())
        node = self.generic_visit(node)
        self.scope_stack.pop()
        return node

    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.AST:
        self.scope_stack.append(set())
        free_vars = self._analyze_free_vars(node)

        if free_vars:
            closure_id = id(node)
            self.closure_cells[closure_id] = [types.CellType() for _ in free_vars]
            self.current_closure = closure_id
            node.body.insert(0, self._create_closure_init(free_vars))

        node = self.generic_visit(node)
        self.scope_stack.pop()
        return node

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_Global(self, node: ast.Global) -> ast.Global:
        return node  # No special handling needed in 3.12+

    def visit_Nonlocal(self, node: ast.Nonlocal) -> ast.Nonlocal:
        return node  # Handled via closure cells

    def visit_Name(self, node: ast.Name) -> ast.AST:
        match node.ctx:
            case ast.Load() if node.id in self.scope_stack[-1]:
                return self._handle_closure_access(node)
            case ast.Store() if node.id.startswith("__pipe_"):
                self.scope_stack[-1].add(node.id)
        return node

    def visit_BinOp(self, node: ast.BinOp) -> ast.AST:
        match node.op:
            case ast.LShift() | ast.RShift():
                return self._transform_pipe(node)
            case _:
                return node

    def _transform_pipe(self, node: ast.BinOp) -> ast.AST:
        match node:
            case ast.BinOp(left=lhs, op=(ast.LShift() | ast.RShift()), right=rhs):
                rhs_call = (
                    rhs
                    if isinstance(rhs, ast.Call)
                    else ast.Call(
                        func=rhs, args=[], keywords=[], lineno=rhs.lineno, col_offset=rhs.col_offset
                    )
                )

                insert_pos = 0 if isinstance(node.op, ast.RShift) else len(rhs_call.args)
                processed_lhs = self._process_lhs(lhs)

                rhs_call.args.insert(insert_pos, processed_lhs)
                return self.visit(rhs_call)
            case _:
                return node

    def _process_lhs(self, lhs: ast.AST) -> ast.AST:
        if not self._is_simple(lhs):
            temp_name = f"__pipe_{uuid.uuid4().hex[:8]}"
            self.temp_registry[temp_name] = ast.Assign(
                targets=[ast.Name(id=temp_name, ctx=ast.Store())], value=lhs
            )
            return ast.Name(id=temp_name, ctx=ast.Load())
        return lhs

    def _is_simple(self, node: ast.AST) -> bool:
        return isinstance(node, (ast.Name, ast.Constant, ast.Attribute, ast.Subscript, ast.Call, ast.UnaryOp))

    def _analyze_free_vars(self, node: ast.FunctionDef) -> list[str]:
        return [
            n.id
            for n in ast.walk(node)
            if isinstance(n, ast.Name)
            and isinstance(n.ctx, ast.Load)
            and n.id not in self.scope_stack[-1]
            and any(n.id in scope for scope in self.scope_stack[:-1])
        ]

    def _create_closure_init(self, free_vars: list[str]) -> ast.Assign:
        return ast.Assign(
            targets=[ast.Name(id=f"__closure_{self.current_closure}", ctx=ast.Store())],
            value=ast.Tuple(
                elts=[
                    ast.Call(
                        func=ast.Name(id="types.CellType", ctx=ast.Load()),
                        args=[ast.Constant(value=None)],
                        keywords=[],
                    )
                    for _ in free_vars
                ],
                ctx=ast.Load(),
            ),
        )

    def _handle_closure_access(self, node: ast.Name) -> ast.AST:
        if self.current_closure is None:
            err = PipeTransformError(f"Undefined closure variable {node.id}")
            err.add_note("Closure access outside of function context")
            raise err

        return ast.Attribute(
            value=ast.Subscript(
                value=ast.Attribute(
                    value=ast.Name(id=f"__closure_{self.current_closure}", ctx=ast.Load()),
                    attr="__cells__",
                    ctx=ast.Load(),
                ),
                slice=ast.Constant(value=0),
                ctx=ast.Load(),
            ),
            attr="value",
            ctx=ast.Load(),
            lineno=node.lineno,
            col_offset=node.col_offset,
        )

    def _inject_temp_vars(self, node: ast.AST) -> ast.AST:
        if isinstance(node, ast.Module) and self.temp_registry:
            node.body = list(self.temp_registry.values()) + node.body
        return node


def pipes(obj: type | Callable) -> type | Callable:
    transformer = PipeTransformer()
    tree = ast.parse(inspect.getsource(obj))
    transformed = transformer.visit(tree)
    transformed = transformer._inject_temp_vars(transformed)

    exec(
        compile(
            transformed,
            sys._getframe(1).f_code.co_filename,
            (ctx := {**sys._getframe(1).f_globals, **sys._getframe(1).f_locals}),
        )
    )
    return ctx[transformed.body[0].name]


@pipes
def test_nonlocal():
    x = 10

    def inner():
        nonlocal x
        x = 20
        return x

    inner()
    return x  # Should return 20
