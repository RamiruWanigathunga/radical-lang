"""
Radical Language Parser and Syntactic Lowering Engine.
Transforms Radical token streams and syntax into valid Python AST and source code.
"""

from typing import Optional
from radical.token import Token, TokenType
from radical.lexer import RadicalLexer
from radical.exceptions import RadicalSyntaxError, RadicalCompileError
from radical.transforms import bindings, declarations, control_flow, concurrency, operators, functional, emitter


class RadicalParser:
    """
    Parses and transforms Radical source code into standard Python code.
    """
    def __init__(self, filename: str = "<string>") -> None:
        self.filename = filename
        self.lexer = RadicalLexer(filename=filename)
        self._pipeline_var_counter = 0
        self._try_counter = 0
        self.explanations: list[str] = []

    def add_explanation(self, lineno: int, message: str) -> None:
        self.explanations.append(f"line {lineno}: {message}")

    def transform_let(self, tokens: list[Token]) -> list[Token]:
        return bindings.transform_let(tokens)

    def transform_tagged_templates(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return operators.transform_tagged_templates(tokens, add_explanation=self.add_explanation)

    def transform_using(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return control_flow.transform_using(tokens, add_explanation=self.add_explanation)

    def transform_unsafe(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return control_flow.transform_unsafe(tokens, add_explanation=self.add_explanation)

    def transform_native_fn(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return declarations.transform_native_fn(tokens, add_explanation=self.add_explanation)

    def transform_struct_with(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return operators.transform_struct_with(tokens, add_explanation=self.add_explanation)

    def transform_enums(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return declarations.transform_enums(tokens, filename=self.filename, add_explanation=self.add_explanation)

    def transform_traits(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return declarations.transform_traits(tokens, filename=self.filename, add_explanation=self.add_explanation)

    def _next_pipeline_var_id(self) -> int:
        self._pipeline_var_counter += 1
        return self._pipeline_var_counter

    def transform_select(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return control_flow.transform_select(
            tokens,
            add_explanation=self.add_explanation,
            var_counter_fn=self._next_pipeline_var_id,
        )

    def _next_try_counter(self) -> int:
        self._try_counter = getattr(self, "_try_counter", 0) + 1
        return self._try_counter

    def transform_try_operator(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return operators.transform_try_operator(
            tokens,
            add_explanation=self.add_explanation,
            counter_fn=self._next_try_counter,
        )

    def transform_const(self, tokens: list[Token]) -> tuple[list[Token], list[tuple[str, int, int]]]:
        return bindings.transform_const(tokens)

    def transform_destructuring(self, tokens: list[Token]) -> tuple[list[Token], list[tuple[str, int, int]]]:
        return bindings.transform_destructuring(tokens)

    def _parse_destruct_field(self, field_tokens: list[Token]) -> tuple[str, str, int, int]:
        return bindings.parse_destruct_field(field_tokens)

    def transform_fn_functions(self, tokens: list[Token]) -> tuple[list[Token], list[tuple[str, int, int]]]:
        return declarations.transform_fn_functions(tokens, filename=self.filename)

    def transform_structs(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return declarations.transform_structs(tokens, filename=self.filename)

    def transform_cartesian_loops(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return concurrency.transform_cartesian_loops(tokens)

    def transform_raw_buffers(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return declarations.transform_raw_buffers(tokens, filename=self.filename)

    def transform_parallel_loops(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return concurrency.transform_parallel_loops(tokens, filename=self.filename, add_explanation=self.add_explanation)

    def transform_gpu_constructs(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return concurrency.transform_gpu_constructs(tokens, filename=self.filename, add_explanation=self.add_explanation)

    def transform_defer(self, tokens: list[Token]) -> tuple[list[Token], bool]:
        return control_flow.transform_defer(tokens)

    def _wrap_function_with_defer(self, body_tokens: list[Token], inner_indent: int) -> list[Token]:
        return control_flow.wrap_function_with_defer(body_tokens, inner_indent)

    def transform_ranges(self, tokens: list[Token]) -> list[Token]:
        return operators.transform_ranges(tokens, filename=self.filename, add_explanation=self.add_explanation)

    def _next_coalesce_counter(self) -> int:
        self._coalesce_counter = getattr(self, "_coalesce_counter", 0) + 1
        return self._coalesce_counter

    def transform_coalescing(self, tokens: list[Token]) -> list[Token]:
        return operators.transform_coalescing(
            tokens,
            filename=self.filename,
            counter_fn=self._next_coalesce_counter,
        )

    def transform_safe_nav(self, tokens: list[Token]) -> list[Token]:
        return operators.transform_safe_nav(tokens, filename=self.filename)

    def transform_arrows(self, tokens: list[Token]) -> list[Token]:
        return functional.transform_arrows(tokens)

    def _extract_arrow_params(self, tokens: list[Token]) -> list[Token]:
        return functional.extract_arrow_params(tokens)

    def _clean_arrow_params(self, tokens: list[Token]) -> list[Token]:
        return functional.clean_arrow_params(tokens)

    def _extract_arrow_body(self, tokens: list[Token], start_idx: int) -> tuple[list[Token], int]:
        return functional.extract_arrow_body(tokens, start_idx)

    def transform_pipelines(self, tokens: list[Token]) -> list[Token]:
        return functional.transform_pipelines(
            tokens,
            filename=self.filename,
            add_explanation=self.add_explanation,
            var_counter_fn=self._next_pipeline_var_id,
        )

    def _process_pipeline_chain(
        self,
        left_tokens: list[Token],
        pipe_steps: list[tuple[Token, list[Token]]],
    ) -> list[Token]:
        return functional.process_pipeline_chain(
            left_tokens,
            pipe_steps,
            add_explanation=self.add_explanation,
            var_counter_fn=self._next_pipeline_var_id,
        )

    def _try_fuse_pipeline_steps(
        self,
        curr_left: list[Token],
        steps: list[tuple[Token, list[Token]]],
    ) -> tuple[Optional[list[Token]], int]:
        return functional.try_fuse_pipeline_steps(
            curr_left,
            steps,
            var_counter_fn=self._next_pipeline_var_id,
        )

    def _is_collector_step(self, step: list[Token]) -> Optional[str]:
        return functional.is_collector_step(step)

    def _parse_filter_step(self, step: list[Token]) -> Optional[list[Token]]:
        return functional.parse_filter_step(step)

    def _parse_map_step(self, step: list[Token]) -> Optional[list[Token]]:
        return functional.parse_map_step(step)

    def _split_top_level_args(self, tokens: list[Token]) -> list[list[Token]]:
        return functional.split_top_level_args(tokens)

    def _try_inline_lambda(self, fn_tokens: list[Token], arg_tokens: list[Token]) -> Optional[list[Token]]:
        return functional.try_inline_lambda(fn_tokens, arg_tokens)

    def _apply_func_tokens(self, fn_tokens: list[Token], arg_tokens: list[Token], line: int, col: int) -> list[Token]:
        return functional.apply_func_tokens(fn_tokens, arg_tokens, line, col)

    def _build_fused_comprehension(
        self,
        curr_left: list[Token],
        filter_preds: list[list[Token]],
        map_funcs: list[list[Token]],
        collector: Optional[str],
        ref_line: int,
        ref_col: int,
    ) -> list[Token]:
        return functional.build_fused_comprehension(
            curr_left=curr_left,
            filter_preds=filter_preds,
            map_funcs=map_funcs,
            collector=collector,
            ref_line=ref_line,
            ref_col=ref_col,
            var_counter_fn=self._next_pipeline_var_id,
        )

    def _extract_pipeline_target(self, tokens: list[Token], start_idx: int) -> tuple[list[Token], int]:
        return functional.extract_pipeline_target(tokens, start_idx)

    def _build_pipeline_call(self, left: list[Token], right: list[Token], pipe_tok: Token) -> list[Token]:
        return functional.build_pipeline_call(left, right, pipe_tok)

    def _extract_left_operand(self, tokens: list[Token]) -> list[Token]:
        return operators.extract_left_operand(tokens)

    def _extract_right_operand(self, tokens: list[Token], start_idx: int) -> tuple[list[Token], int]:
        return operators.extract_right_operand(tokens, start_idx)

    def _build_range_tokens(
        self,
        left_tokens: list[Token],
        right_tokens: list[Token],
        step_tokens: Optional[list[Token]],
        inclusive: bool,
        ref_tok: Token,
    ) -> list[Token]:
        return operators.build_range_tokens(
            left_tokens=left_tokens,
            right_tokens=right_tokens,
            step_tokens=step_tokens,
            inclusive=inclusive,
            ref_tok=ref_tok,
        )

    def tokens_to_source(self, tokens: list[Token]) -> str:
        return emitter.tokens_to_source(tokens)
