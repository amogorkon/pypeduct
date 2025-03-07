from ast import (
    AST,
    Assign,
    Attribute,
    BinOp,
    Call,
    Constant,
    FunctionDef,
    Load,
    Name,
    NamedExpr,
    NodeTransformer,
    Return,
    RShift,
    Starred,
    Store,
    expr,
    keyword,
    stmt,
)
from collections.abc import Sequence
import inspect
from typing import Callable, final, get_type_hints, override

from pypeduct.exceptions import PipeTransformError
from pypeduct.helpers import NODE, ensure_loc, should_unpack


@final
class PipeTransformer(NodeTransformer):
    def __init__(self, hofs: dict[str, Callable], current_globals=None) -> None:
        self.current_block_assignments: list[Assign] = []
        self.function_params = {}
        self.hofs = hofs
        self.current_globals = current_globals or {}

    @override
    def visit(
        self, node: AST
    ) -> AST | list[AST] | None:  # sourcery skip: extract-method
        match node:
            case FunctionDef(name, args, body, decorator_list):
                self.function_params[name] = (
                    len(args.posonlyargs) + len(args.args),
                    args.vararg is not None,
                )
                processed_body = self.process_body(body)
                return ensure_loc(
                    FunctionDef(name, args, processed_body, decorator_list), node
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
        if isinstance(left, Constant) and left.value is Ellipsis:
            raise PipeTransformError(
                "Why would you put a `...` on the left side of the pipe? 🤔",
            )

        def _is_ellipsis_placeholder(node):
            return isinstance(node, Constant) and node.value is Ellipsis

        match right:
            case Call(func, args, keywords) if (
                placeholder_num := (
                    sum(_is_ellipsis_placeholder(arg) for arg in args)
                    + sum(_is_ellipsis_placeholder(kw.value) for kw in keywords)
                )
            ) > 0:
                if placeholder_num > 1:
                    raise PipeTransformError(
                        "Only one argument position placeholder `...` is allowed in a pipe expression",
                    )
                new_args = [
                    (
                        left
                        if isinstance(arg, Constant) and arg.value is Ellipsis
                        else arg
                    )
                    for arg in args
                ]
                new_keywords = []
                for kw in keywords:
                    if isinstance(kw.value, Constant) and kw.value.value is Ellipsis:
                        new_keywords.append(keyword(arg=kw.arg, value=left))
                    else:
                        new_keywords.append(kw)
                return ensure_loc(Call(func, new_args, new_keywords), node)
            case Call(Name(id=name), args, keywords) if name in self.hofs:
                return ensure_loc(
                    Call(Name(name, Load()), args + [left], keywords),
                    node,
                )

            case Call(
                Attribute(value=Name(id=mod), attr=attr, ctx=Load()),
                args,
                keywords,
            ) if f"{mod}.{attr}" in self.hofs:
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

            # normal function call, unpack by default if first argument is not specified or not a sequence
            case Call(func, args, keywords):
                # Determine whether we should star-unpack the piped value
                star = False
                func_obj = None

                # Try to resolve the function object using our current globals.
                if isinstance(func, Name):
                    func_obj = self.current_globals.get(func.id)
                elif isinstance(func, Attribute):
                    # Try by attribute name. You might also want to try building a fully-qualified name.
                    func_obj = self.current_globals.get(func.attr)

                if func_obj is not None:
                    try:
                        sig = inspect.signature(func_obj)
                        params = list(sig.parameters.values())
                        if params:
                            first_param = params[0]
                            # Use get_type_hints to resolve annotations.
                            hints = get_type_hints(func_obj)
                            annotation = hints.get(
                                first_param.name, first_param.annotation
                            )
                            # If there is an annotation, and it indicates a kind of Sequence
                            # (but is not a str or bytes), then we star-unpack.
                            if (
                                annotation is not inspect.Parameter.empty
                                and isinstance(annotation, type)
                                and issubclass(annotation, Sequence)
                                and annotation not in (str, bytes)
                            ):
                                star = True
                    except Exception:
                        # If anything fails, leave 'star' as False.
                        pass

                if star:
                    new_args = [Starred(left, ctx=Load())] + args
                else:
                    new_args = [left] + args

                return ensure_loc(Call(func, new_args, keywords), node)

            # Variadic functions
            case Name(id=name) if name in self.function_params:
                _, has_varargs = self.function_params[name]
                args = [Starred(left, ctx=Load())] if has_varargs else [left]
                return ensure_loc(Call(right, args, []), node)

            case _:
                return ensure_loc(Call(right, [left], []), node)

    def process_body(self, body: list[stmt]) -> Sequence[NODE]:
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
