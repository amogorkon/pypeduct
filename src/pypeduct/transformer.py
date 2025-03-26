# transformer.py
from ast import (
    AST,
    Assign,
    AsyncFunctionDef,
    Attribute,
    BinOp,
    Call,
    Constant,
    FunctionDef,
    Global,
    Lambda,
    Load,
    Name,
    NamedExpr,
    NodeTransformer,
    Nonlocal,
    Return,
    RShift,
    Store,
    expr,
    keyword,
    stmt,
)
from typing import Callable, NamedTuple, final, override

from pypeduct.exceptions import PipeTransformError
from pypeduct.helpers import (
    ensure_loc,
    get_num_required_args,
    inject_unpack_helper,
)


class FunctionParams(NamedTuple):
    num_required: int
    num_pos: int


@final
class PipeTransformer(NodeTransformer):
    def __init__(self, hofs: dict[str, Callable], context=None, verbose=False) -> None:
        super().__init__()
        self.verbose = verbose
        self.current_block_assignments: list[Assign] = []
        self.function_params: dict[str, FunctionParams] = {}
        self.hofs = hofs
        self.context = context or {}
        self.processing_function = False
        self.current_function_level = 0

    def process_body(self, body: list[stmt]) -> list[AST]:
        original_assignments = self.current_block_assignments
        self.current_block_assignments = []
        processed = []
        for stmt_node in body:
            result = self.visit(stmt_node)
            if isinstance(result, list):
                processed.extend(result)
            else:
                processed.append(result)
        return original_assignments + processed

    def print(self, msg: str) -> None:
        if self.verbose:
            print(f"[DEBUG] {msg}")

    @override
    def visit(self, node: AST) -> AST | list[AST] | None:
        match node:
            case FunctionDef(name, args, body, decorator_list) | AsyncFunctionDef(
                name, args, body, decorator_list
            ):
                original_level = self.current_function_level
                self.current_function_level += 1
                scoping_stmts = [
                    stmt for stmt in body if isinstance(stmt, (Nonlocal, Global))
                ]
                other_stmts = [
                    stmt for stmt in body if not isinstance(stmt, (Nonlocal, Global))
                ]

                try:
                    if self.current_function_level == 1:
                        self.function_params[name] = FunctionParams(
                            num_required=max(
                                0,
                                (
                                    len(args.posonlyargs)
                                    + len(args.args)
                                    - len(args.defaults)
                                ),
                            ),
                            num_pos=len(args.posonlyargs) + len(args.args),
                        )

                    processed_body = self.process_body(other_stmts)
                    new_body = scoping_stmts + inject_unpack_helper(
                        scoping_stmts + processed_body
                    )

                finally:
                    self.current_function_level = original_level

                if isinstance(node, FunctionDef):
                    return ensure_loc(
                        FunctionDef(name, args, new_body, decorator_list), node
                    )
                return ensure_loc(
                    AsyncFunctionDef(name, args, new_body, decorator_list), node
                )

            case BinOp(
                left,
                RShift(),
                NamedExpr(target=Name(id=var_name, ctx=Store()), value=value),
            ):
                next_left = self.visit(left)
                next_value = self.visit(value)
                if isinstance(next_value, Call):
                    new_args = next_value.args + [next_left]
                    new_call = ensure_loc(
                        Call(next_value.func, new_args, next_value.keywords), node
                    )
                else:
                    new_call = ensure_loc(Call(next_value, [next_left], []), node)
                return ensure_loc(
                    NamedExpr(target=Name(id=var_name, ctx=Store()), value=new_call),
                    node,
                )

            case BinOp(left, RShift(), right):
                return self.build_pipe_call(node, self.visit(left), self.visit(right))

            case Return(value):
                processed_value = self.visit(value)
                return [
                    *self.current_block_assignments,
                    ensure_loc(Return(value=processed_value), node),
                ]

            case _:
                return self.generic_visit(node)

    def build_pipe_call(self, node: BinOp, left: expr, right: expr) -> Call:
        def is_ellipsis(node):
            return isinstance(node, Constant) and node.value is Ellipsis

        if is_ellipsis(left):
            raise PipeTransformError(
                "Why would you put a `...` on the left side of the pipe? 🤔"
            )

        match right:
            case Call(func, args, keywords) if (
                placeholder_num := (
                    sum(map(is_ellipsis, args))
                    + sum(is_ellipsis(kw.value) for kw in keywords)
                )
            ) > 0:
                if placeholder_num > 1:
                    raise PipeTransformError(
                        "Only one argument position placeholder `...` is allowed in a pipe expression"
                    )
                self.print(
                    f"Placeholder case ({args}, {keywords}): {left} into {right}"
                )
                new_args = [left if is_ellipsis(arg) else arg for arg in args]
                new_keywords = [
                    keyword(kw.arg, left) if is_ellipsis(kw.value) else kw
                    for kw in keywords
                ]
                return ensure_loc(Call(func, new_args, new_keywords), node)

            case Call(Name(id=name), args, keywords) if name in self.hofs:
                self.print(f"HOF case short name ({name} in hofs): {name}")
                return ensure_loc(
                    Call(Name(name, Load()), args + [left], keywords), node
                )

            case Call(
                Attribute(value=Name(id=mod), attr=attr, ctx=Load()),
                args,
                keywords,
            ) if f"{mod}.{attr}" in self.hofs:
                self.print(f"HOF qualname ({mod}.{attr} in hofs)")
                return ensure_loc(
                    Call(
                        Attribute(
                            value=Name(id=mod, ctx=Load()), attr=attr, ctx=Load()
                        ),
                        args + [left],
                        keywords,
                    ),
                    node,
                )

            case Call(func, args, keywords):
                self.print(f"Regular case: {left} into {right}")
                num_req = get_num_required_args(
                    func, self.function_params, self.context
                )
                return ensure_loc(
                    Call(
                        Name("_pyped_unpack", Load()),
                        [left, Constant(num_req), func, *args],
                        keywords,
                    ),
                    node,
                )

            case Name(id=name) if name in self.function_params:
                self.print(f"Variadic case: {name=} in {self.function_params=}")
                num_req = self.function_params[name].num_required
                return ensure_loc(
                    Call(
                        Name("_pyped_unpack", Load()),
                        [left, Constant(num_req), right],
                        [],
                    ),
                    node,
                )

            case Lambda(args=lambda_args):
                self.print(f"Lambda case: {left} ↦ {right}")
                num_req = len(lambda_args.posonlyargs) + len(lambda_args.args)
                return ensure_loc(
                    Call(
                        Name("_pyped_unpack", Load()),
                        [left, Constant(num_req), right],
                        [],
                    ),
                    node,
                )

            case _:
                num_req = get_num_required_args(
                    right, self.function_params, self.context
                )
                self.print(f"Fall-through: {left} ↦ {right}, {num_req=}")
                return ensure_loc(
                    Call(
                        Name("_pyped_unpack", Load()),
                        [left, Constant(num_req), right],
                        [],
                    ),
                    node,
                )
