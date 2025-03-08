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
from pypeduct.helpers import ensure_loc, is_seq_ast, is_seq_runtime, resolve_attribute


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
                unpack = self._should_unpack(func, left)
                new_args = [Starred(left, Load())] + args if unpack else [left] + args
                return ensure_loc(Call(func, new_args, keywords), node)

            case Name(id=name) if name in self.function_params:
                self.print(f"Variadic case: {name=} in {self.function_params=}")
                unpack = (
                    isinstance(left, Tuple)
                    and not self._has_sequence_annotation(right)
                    and self.function_params[name].num_pos != 1
                )
                args = [Starred(left, ctx=Load())] if unpack else [left]
                return ensure_loc(Call(right, args, []), node)

            case Lambda(args=lambda_args):
                num_pos = len(lambda_args.posonlyargs) + len(lambda_args.args)
                has_seq_annot = self._has_sequence_annotation(right)
                unpack = isinstance(left, Tuple) and not has_seq_annot and num_pos != 1
                return ensure_loc(
                    Call(right, [Starred(left, Load())] if unpack else [left], []), node
                )

            case _:  # actually very common because it covers all the functions outside the decorated context
                unpack = isinstance(left, Tuple) and not self._is_single_arg_func(right)
                args = [Starred(left, Load())] if unpack else [left]
                self.print(f"Fall-through case: {left} into {right}, {unpack=}")
                return ensure_loc(Call(right, args, []), node)

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

    def _should_unpack(self, func_node: AST, left: expr) -> bool:
        """Decides if `left` should be unpacked when passed to `func_node`."""
        if isinstance(left, Constant) and isinstance(
            left.value, (str, bytes, int, float)
        ):
            return False

        if self._is_single_arg_func(func_node):
            return False

        return isinstance(left, Tuple)

    def _get_required_params(self, func_node: AST) -> int:
        """Count positional parameters without default values."""
        match func_node:
            case Name(id=name) if name in self.function_params:
                params = self.function_params[name]
                return params.num_pos - params.defaults_count
            case Lambda(args=lambda_args):
                return len(lambda_args.posonlyargs) + len(lambda_args.args)
        return 1

    def _is_single_arg_func(self, func_node: AST) -> bool:
        """Check if function expects exactly 1 positional argument."""
        try:
            if isinstance(func_node, Name):
                if func_obj := self.current_globals.get(func_node.id):
                    try:
                        sig = inspect.signature(func_obj)
                    except ValueError:
                        # Built-in without signature - assume multi-arg
                        return False
                    params = list(sig.parameters.values())
                    num_required = sum(
                        p.default is inspect.Parameter.empty
                        and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                        for p in params
                    )
                    return num_required == 1

            elif isinstance(func_node, Attribute):
                func = resolve_attribute(func_node, self.current_globals)
                if not func:
                    return False

                try:
                    sig = inspect.signature(func)
                except ValueError:
                    # Built-in without signature - assume multi-arg
                    return False

                params = list(sig.parameters.values())
                num_required = sum(
                    p.default is inspect.Parameter.empty
                    and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
                    for p in params
                )
                return num_required == 1

        except Exception:
            pass

        return False

    def _has_sequence_annotation(self, func_node: AST) -> bool:
        """Check if first parameter expects a sequence using AST and runtime info."""
        # Local functions (defined in decorated scope)
        if isinstance(func_node, Name) and func_node.id in self.function_params:
            func_info = self.function_params[func_node.id]
            if not func_info.param_annotations:
                return False
            ann = func_info.param_annotations[0]
            return is_seq_ast(ann) or is_seq_runtime(ann)

        # Lambdas
        if isinstance(func_node, Lambda) and func_node.args.args:
            ann = func_node.args.args[0].annotation
            return is_seq_ast(ann) or is_seq_runtime(ann)

        # External functions (using resolve_attribute)
        if isinstance(func_node, (Name, Attribute)):
            func_obj = None
            if isinstance(func_node, Name):
                func_obj = self.current_globals.get(func_node.id)
            elif isinstance(func_node, Attribute):
                func_obj = resolve_attribute(func_node, self.current_globals)

            if func_obj and hasattr(func_obj, "__annotations__"):
                params = list(inspect.signature(func_obj).parameters.values())
                # Skip self/cls for bound methods
                offset = 1 if hasattr(func_obj, "__self__") else 0
                if params[offset:]:
                    ann_type = func_obj.__annotations__.get(params[offset].name)
                    return is_seq_runtime(ann_type)

        return False

    def get_runtime_function(self, node: AST) -> Callable | None:
        match node:
            case Name(id=name) if name in self.current_globals:
                return self.current_globals[name]

            case Attribute(value=Constant(value=const_val), attr=attr):
                # Resolve methods on literal constants like " ".join -> str.join
                method = getattr(type(const_val), attr, None)
                if method and callable(method):
                    return method.__get__(const_val)

        return None
