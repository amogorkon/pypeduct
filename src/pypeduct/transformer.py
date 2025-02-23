from __future__ import annotations

import ast


class PipeTransformError(Exception):
    """Custom exception for pipe transformation errors."""


class PipeTransformer(ast.NodeTransformer):
    def visit_BinOp(self, node):
        if not isinstance(node.op, (ast.LShift, ast.RShift)):
            return node
        if not isinstance(node.right, ast.Call):
            return self.visit(
                ast.Call(
                    func=node.right,
                    args=[node.left],
                    keywords=[],
                    lineno=node.right.lineno,
                    col_offset=node.right.col_offset,
                )
            )
        node.right.args.insert(
            0 if isinstance(node.op, ast.RShift) else len(node.right.args), node.left
        )
        return self.visit(node.right)
