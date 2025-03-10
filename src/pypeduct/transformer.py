import inspect
from ast import (
    AST,
    Assign,
    Attribute,
    BinOp,
    Call,
    Constant,
    FunctionDef,
    Lambda,
    Load,
    Name,
    NamedExpr,
    NodeTransformer,
    Return,
    RShift,
    Starred,
    Store,
    Tuple,
    expr,
    keyword,
    stmt,
)
from typing import Callable, NamedTuple, final, override

from pypeduct.exceptions import PipeTransformError
from pypeduct.helpers import (
    ensure_loc,
    has_sequence_annotation,
    is_single_arg_func,
    resolve_attribute,
    should_unpack,
)


class FunctionParams(NamedTuple):
    num_pos: int
    has_varargs: bool
    param_annotations: list[AST | None]
    defaults_count: int


@final
class PipeTransformer(NodeTransformer):
    def __init__(
        self, hofs: dict[str, Callable], current_globals=None, verbose=False
    ) -> None:
        self.verbose = verbose
        self.current_block_assignments: list[Assign] = []
        self.function_params: dict[str, FunctionParams] = {}
        self.hofs = hofs
        self.current_globals = current_globals or {}

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
            case FunctionDef(name, args, body, decorator_list):
                self.function_params[name] = FunctionParams(
                    num_pos=len(args.posonlyargs) + len(args.args),
                    has_varargs=args.vararg is not None,
                    param_annotations=[
                        arg.annotation for arg in args.posonlyargs + args.args
                    ],
                    defaults_count=len(args.defaults) if args.defaults else 0,
                )
                processed_body = self.process_body(body)
                return ensure_loc(
                    FunctionDef(name, args, processed_body, decorator_list),
                    node,
                )

            case BinOp(
                left,
                RShift(),
                NamedExpr(target=Name(id=var_name, ctx=Store()), value=value),
            ):
                next_left = self.visit(left)
                next_value = self.visit(value)
                if isinstance(next_value, Call):
                    new_args = [next_left] + next_value.args
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
                unpack = should_unpack(func, left, self.current_globals)
                new_args = [Starred(left, Load())] + args if unpack else [left] + args
                return ensure_loc(Call(func, new_args, keywords), node)

            case Name(id=name) if name in self.function_params:
                self.print(f"Variadic case: {name=} in {self.function_params=}")
                unpack = (
                    isinstance(left, Tuple)
                    and not has_sequence_annotation(
                        right, self.function_params, self.current_globals
                    )
                    and self.function_params[name].num_pos != 1
                )
                args = [Starred(left, ctx=Load())] if unpack else [left]
                return ensure_loc(Call(right, args, []), node)

            case Lambda(args=lambda_args):
                num_pos = len(lambda_args.posonlyargs) + len(lambda_args.args)
                has_seq_annot = has_sequence_annotation(
                    right, self.function_params, self.current_globals
                )
                unpack = isinstance(left, Tuple) and not has_seq_annot and num_pos != 1
                return ensure_loc(
                    Call(right, [Starred(left, Load())] if unpack else [left], []), node
                )

            case _:  # actually very common because it covers all the functions outside the decorated context
                unpack = isinstance(left, Tuple) and not is_single_arg_func(
                    right, self.current_globals
                )
                args = [Starred(left, Load())] if unpack else [left]
                self.print(f"Fall-through case: {left} into {right}, {unpack=}")
                return ensure_loc(Call(right, args, []), node)
