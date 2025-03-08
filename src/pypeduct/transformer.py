from ast import (
    AST,
    Assign,
    Attribute,
    BinOp,
    Call,
    Constant,
    FunctionDef,
    GeneratorExp,
    Lambda,
    List,
    Load,
    Name,
    NamedExpr,
    NodeTransformer,
    Return,
    RShift,
    Set,
    Starred,
    Store,
    Tuple,
    expr,
    keyword,
    stmt,
)
from typing import Callable, NamedTuple, final, override

from pypeduct.exceptions import PipeTransformError
from pypeduct.helpers import ensure_loc, is_seq_ast, is_seq_runtime


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
        def _is_ellipsis_placeholder(node):
            return isinstance(node, Constant) and node.value is Ellipsis

        if isinstance(left, Constant) and left.value is Ellipsis:
            raise PipeTransformError(
                "Why would you put a `...` on the left side of the pipe? 🤔"
            )

        match right:
            # Handle placeholder usage.
            case Call(func, args, keywords) if (
                placeholder_num := (
                    sum(_is_ellipsis_placeholder(arg) for arg in args)
                    + sum(_is_ellipsis_placeholder(kw.value) for kw in keywords)
                )
            ) > 0:
                if placeholder_num > 1:
                    raise PipeTransformError(
                        "Only one argument position placeholder `...` is allowed in a pipe expression"
                    )
                self.print(
                    f"Placeholder case ({args}, {keywords}): {left} into {right}"
                )
                new_args = [
                    left
                    if (isinstance(arg, Constant) and arg.value is Ellipsis)
                    else arg
                    for arg in args
                ]
                new_keywords = []
                for kw in keywords:
                    if isinstance(kw.value, Constant) and kw.value.value is Ellipsis:
                        new_keywords.append(keyword(arg=kw.arg, value=left))
                    else:
                        new_keywords.append(kw)
                return ensure_loc(Call(func, new_args, new_keywords), node)

            # Higher-order function (HOF) cases.
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

            # Regular function call.
            case Call(func, args, keywords):
                self.print(f"Regular case: {left} into {right}")
                if self._should_unpack(func_node=func, left=left):
                    new_args = [Starred(left, ctx=Load())] + args
                else:
                    new_args = [left] + args
                return ensure_loc(Call(func, new_args, keywords), node)

            # Variadic case: when right is a Name and stored in function_params.
            case Name(id=name) if name in self.function_params:
                self.print(f"Variadic case: {name=} in {self.function_params=}")
                func_info = self.function_params[name]
                # Use static metadata to decide.
                unpack = (
                    isinstance(left, (Tuple, List, Set, GeneratorExp))
                    and func_info.num_pos > 1
                    and not func_info.has_varargs
                    and not self._has_sequence_annotation(func_info)
                )
                args = [Starred(left, ctx=Load())] if unpack else [left]
                return ensure_loc(Call(right, args, []), node)

            # Lambda: use lambda parameters.
            case Lambda(args=lambda_args):
                self.print(f"Lambda case: {lambda_args=}")
                num_pos = len(lambda_args.posonlyargs) + len(lambda_args.args)
                has_varargs = lambda_args.vararg is not None
                hint = lambda_args.args[0].annotation if lambda_args.args else None
                unpack = (
                    (not is_seq_ast(hint))
                    if hint
                    else (num_pos > 1 and not has_varargs)
                )
                args = [Starred(left, ctx=Load())] if unpack else [left]
                return ensure_loc(Call(right, args, []), node)

            case _:
                self.print(f"Fall-through case: {left} into {right}")
                return ensure_loc(Call(right, [left], []), node)

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

    def _has_varargs(self, func_node: AST) -> bool:
        match func_node:
            case Name(id=name) if name in self.function_params:
                return self.function_params[name].has_varargs
            case Lambda(args=lambda_args):
                return lambda_args.vararg is not None
        return False

    def _expected_positional_args(self, func_node: AST) -> int:
        match func_node:
            case Name(id=name) if name in self.function_params:
                return self.function_params[name].num_pos
            case Lambda(args=lambda_args):
                return len(lambda_args.posonlyargs) + len(lambda_args.args)
        return 1

    def _has_sequence_annotation(self, func_info: FunctionParams) -> bool:
        if not func_info.param_annotations:
            return False
        first_annotation = func_info.param_annotations[0]
        return is_seq_ast(first_annotation) or is_seq_runtime(first_annotation)

    def _should_unpack(self, func_node: AST, left: expr) -> bool:
        """Decides if `left` should be unpacked when passed to `func_node`."""
        # Avoid unpacking for atomic (non-sequence) constants.
        if isinstance(left, Constant) and isinstance(
            left.value, (str, bytes, int, float)
        ):
            return False

        # Determine how many positional parameters (without defaults) the function requires.
        req_params = self._get_required_params(func_node)

        # Try to extract static metadata, if available.
        func_info = None
        match func_node:
            case Name(id=name) if name in self.function_params:
                func_info = self.function_params[name]
            case _:
                func_info = None

        if func_info is not None:
            has_seq_annot = self._has_sequence_annotation(func_info)
        else:
            # Fallback to lambda analyses.
            if isinstance(func_node, Lambda) and func_node.args.args:
                hint = func_node.args.args[0].annotation
                has_seq_annot = is_seq_ast(hint) or is_seq_runtime(hint)
            else:
                has_seq_annot = False

        # Decide whether to unpack:
        # Only if left is a sequence literal (Tuple, List, or GeneratorExp), its number of elements exactly
        # equals the number of required parameters, and the first parameter is not annotated as a sequence.
        is_unpack_needed = (
            isinstance(left, (Tuple, List, GeneratorExp))
            and hasattr(left, "elts")
            and (len(left.elts) == req_params)
            and not has_seq_annot
        )

        self.print(
            f"Checking unpack: {left} into {func_node} | Req params: {req_params} | Needs unpacking: {is_unpack_needed}"
        )
        return is_unpack_needed

    def _get_required_params(self, func_node: AST) -> int:
        """Count positional parameters without default values."""
        match func_node:
            case Name(id=name) if name in self.function_params:
                params = self.function_params[name]
                return params.num_pos - params.defaults_count
            case Lambda(args=lambda_args):
                return len(lambda_args.posonlyargs) + len(lambda_args.args)
        return 1
