"""
Functional transformations for Radical: arrow functions, pipelines, and step fusion.
"""

from typing import Optional, Callable
from radical.lexer import Token, TokenType
from radical.exceptions import RadicalSyntaxError
from radical.transforms.operators import extract_left_operand


def clean_arrow_params(tokens: list[Token]) -> list[Token]:
    """Strips type annotations from arrow parameter tokens."""
    clean: list[Token] = []
    skip_type = False
    depth = 0

    for tok in tokens:
        if tok.value in ("(", "[", "{"):
            depth += 1
        elif tok.value in (")", "]", "}"):
            depth -= 1

        if depth == 0 and tok.value == ":":
            skip_type = True
            continue
        if depth == 0 and tok.value == ",":
            skip_type = False
            clean.append(tok)
            continue

        if not skip_type:
            clean.append(tok)

    return clean


def extract_arrow_params(tokens: list[Token]) -> list[Token]:
    """Extracts parameters on the left side of `=>`."""
    if not tokens:
        return []

    # Check if left side is parenthesized: (a, b) or ()
    if tokens[-1].value == ")":
        depth = 0
        collected: list[Token] = []
        while tokens:
            tok = tokens.pop()
            if tok.value == ")":
                depth += 1
            elif tok.value == "(":
                depth -= 1
                if depth == 0:
                    break
            if depth > 0 and tok.value != ")":
                collected.insert(0, tok)

        clean_params = clean_arrow_params(collected)
        return clean_params

    # Single identifier: `x => expr`
    if tokens[-1].type == TokenType.IDENTIFIER:
        return [tokens.pop()]

    return []


def extract_arrow_body(tokens: list[Token], start_idx: int) -> tuple[list[Token], int]:
    """Scans forward to extract the full expression body of an arrow function (=>)."""
    body: list[Token] = []
    i = start_idx
    n = len(tokens)
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.OP:
            if tok.value == "(":
                paren_depth += 1
            elif tok.value == ")":
                if paren_depth == 0:
                    break
                paren_depth -= 1
            elif tok.value == "[":
                bracket_depth += 1
            elif tok.value == "]":
                if bracket_depth == 0:
                    break
                bracket_depth -= 1
            elif tok.value == "{":
                brace_depth += 1
            elif tok.value == "}":
                if brace_depth == 0:
                    break
                brace_depth -= 1

        if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            if tok.type == TokenType.PIPE:
                break
            if tok.type in (TokenType.NEWLINE, TokenType.EOF):
                break
            if tok.type in (TokenType.OP, TokenType.DELIMITER) and tok.value in (",", ";"):
                break

        body.append(tok)
        i += 1

    return body, i


def transform_arrows(tokens: list[Token]) -> list[Token]:
    """
    Transforms arrow function tokens:
    - `(a, b) => expr` into `lambda a, b: expr`
    - `x => expr` into `lambda x: expr`
    - `() => expr` into `lambda: expr`
    """
    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.ARROW:
            params_tokens = extract_arrow_params(result)
            i += 1
            body_tokens, next_i = extract_arrow_body(tokens, i)

            lambda_tokens: list[Token] = [
                Token(TokenType.DELIMITER, "(", tok.line, tok.col),
                Token(TokenType.IDENTIFIER, "lambda", tok.line, tok.col)
            ]
            if params_tokens:
                lambda_tokens.append(Token(TokenType.DELIMITER, " ", tok.line, tok.col))
                lambda_tokens.extend(params_tokens)
            lambda_tokens.append(Token(TokenType.DELIMITER, ":", tok.line, tok.col))
            lambda_tokens.append(Token(TokenType.DELIMITER, " ", tok.line, tok.col))
            lambda_tokens.extend(body_tokens)
            lambda_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))

            result.extend(lambda_tokens)
            i = next_i
            continue

        result.append(tok)
        i += 1

    return result


def split_top_level_args(tokens: list[Token]) -> list[list[Token]]:
    args: list[list[Token]] = []
    curr: list[Token] = []
    p_depth = 0
    b_depth = 0
    br_depth = 0
    for tok in tokens:
        if tok.value == "(":
            p_depth += 1
        elif tok.value == ")":
            p_depth -= 1
        elif tok.value == "[":
            b_depth += 1
        elif tok.value == "]":
            b_depth -= 1
        elif tok.value == "{":
            br_depth += 1
        elif tok.value == "}":
            br_depth -= 1
        elif tok.value == "," and p_depth == 0 and b_depth == 0 and br_depth == 0:
            if curr:
                args.append(curr)
                curr = []
            continue
        curr.append(tok)
    if curr:
        args.append(curr)
    return args


def parse_filter_step(step: list[Token]) -> Optional[list[Token]]:
    if len(step) < 3 or step[0].value != "filter" or step[1].value != "(" or step[-1].value != ")":
        return None
    args = split_top_level_args(step[2:-1])
    if len(args) == 1:
        return args[0]
    if len(args) == 2:
        if len(args[1]) == 1 and args[1][0].type == TokenType.IDENTIFIER and args[1][0].value == "_":
            return args[0]
        if len(args[0]) == 1 and args[0][0].type == TokenType.IDENTIFIER and args[0][0].value == "_":
            return args[1]
    return None


def parse_map_step(step: list[Token]) -> Optional[list[Token]]:
    if len(step) < 3 or step[0].value != "map" or step[1].value != "(" or step[-1].value != ")":
        return None
    args = split_top_level_args(step[2:-1])
    if len(args) == 1:
        return args[0]
    if len(args) == 2:
        if len(args[1]) == 1 and args[1][0].type == TokenType.IDENTIFIER and args[1][0].value == "_":
            return args[0]
        if len(args[0]) == 1 and args[0][0].type == TokenType.IDENTIFIER and args[0][0].value == "_":
            return args[1]
    return None


def is_collector_step(step: list[Token]) -> Optional[str]:
    valid_collectors = {"list", "set", "tuple", "sum", "any", "all", "min", "max"}
    if len(step) == 1 and step[0].value in valid_collectors:
        return step[0].value
    if len(step) == 3 and step[0].value in valid_collectors and step[1].value == "(" and step[2].value == ")":
        return step[0].value
    return None


def try_inline_lambda(fn_tokens: list[Token], arg_tokens: list[Token]) -> Optional[list[Token]]:
    """Inlines simple single-parameter lambdas to eliminate closure allocation overhead."""
    toks = [t for t in fn_tokens if t.value.strip()]
    while toks and toks[0].value == "(" and toks[-1].value == ")":
        depth = 0
        is_matching = True
        for t in toks[:-1]:
            if t.value == "(":
                depth += 1
            elif t.value == ")":
                depth -= 1
            if depth == 0:
                is_matching = False
                break
        if is_matching and depth == 1:
            toks = toks[1:-1]
        else:
            break

    if len(toks) >= 4 and toks[0].value == "lambda" and toks[1].type == TokenType.IDENTIFIER and toks[2].value == ":":
        param_name = toks[1].value
        body_tokens = toks[3:]
        if any(t.value == "lambda" for t in body_tokens):
            return None
        inlined: list[Token] = []
        for t in body_tokens:
            if t.type == TokenType.IDENTIFIER and t.value == param_name:
                inlined.extend(arg_tokens)
            else:
                inlined.append(t)
        return inlined
    return None


def apply_func_tokens(fn_tokens: list[Token], arg_tokens: list[Token], line: int, col: int) -> list[Token]:
    inlined = try_inline_lambda(fn_tokens, arg_tokens)
    if inlined is not None:
        return [Token(TokenType.DELIMITER, "(", line, col)] + inlined + [Token(TokenType.DELIMITER, ")", line, col)]

    is_complex = any(t.value in ("lambda", "def") or t.type == TokenType.OP for t in fn_tokens)
    already_paren = fn_tokens and fn_tokens[0].value == "(" and fn_tokens[-1].value == ")"
    res: list[Token] = []
    if is_complex and not already_paren:
        res.append(Token(TokenType.DELIMITER, "(", line, col))
        res.extend(fn_tokens)
        res.append(Token(TokenType.DELIMITER, ")", line, col))
    else:
        res.extend(fn_tokens)
    res.append(Token(TokenType.DELIMITER, "(", line, col))
    res.extend(arg_tokens)
    res.append(Token(TokenType.DELIMITER, ")", line, col))
    return res


def build_fused_comprehension(
    curr_left: list[Token],
    filter_preds: list[list[Token]],
    map_funcs: list[list[Token]],
    collector: Optional[str],
    ref_line: int,
    ref_col: int,
    var_counter_fn: Optional[Callable[[], int]] = None,
) -> list[Token]:
    var_id = var_counter_fn() if var_counter_fn else 1
    var_name = f"_rad_x{var_id}"
    elem_tok = Token(TokenType.IDENTIFIER, var_name, ref_line, ref_col)

    # Build mapped expression
    if not map_funcs:
        mapped_tokens = [elem_tok]
    else:
        curr_expr = [elem_tok]
        for m_tokens in map_funcs:
            curr_expr = apply_func_tokens(m_tokens, curr_expr, ref_line, ref_col)
        mapped_tokens = curr_expr

    # Build filter condition
    cond_tokens: list[Token] = []
    if filter_preds:
        cond_parts: list[list[Token]] = []
        for p_tokens in filter_preds:
            if len(p_tokens) == 1 and p_tokens[0].value == "None":
                cond_parts.append([
                    Token(TokenType.IDENTIFIER, "bool", ref_line, ref_col),
                    Token(TokenType.DELIMITER, "(", ref_line, ref_col),
                    elem_tok,
                    Token(TokenType.DELIMITER, ")", ref_line, ref_col),
                ])
            else:
                cond_parts.append(apply_func_tokens(p_tokens, [elem_tok], ref_line, ref_col))

        if len(cond_parts) == 1:
            cond_tokens = cond_parts[0]
        else:
            for idx, part in enumerate(cond_parts):
                if idx > 0:
                    cond_tokens.append(Token(TokenType.IDENTIFIER, "and", ref_line, ref_col))
                cond_tokens.append(Token(TokenType.DELIMITER, "(", ref_line, ref_col))
                cond_tokens.extend(part)
                cond_tokens.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))

    # Assemble inner comprehension
    inner: list[Token] = []
    inner.extend(mapped_tokens)
    inner.append(Token(TokenType.IDENTIFIER, "for", ref_line, ref_col))
    inner.append(elem_tok)
    inner.append(Token(TokenType.IDENTIFIER, "in", ref_line, ref_col))
    inner.append(Token(TokenType.DELIMITER, "(", ref_line, ref_col))
    inner.extend(curr_left)
    inner.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))
    if cond_tokens:
        inner.append(Token(TokenType.IDENTIFIER, "if", ref_line, ref_col))
        inner.extend(cond_tokens)

    # Wrap with collector
    if collector == "list":
        return [Token(TokenType.DELIMITER, "[", ref_line, ref_col)] + inner + [Token(TokenType.DELIMITER, "]", ref_line, ref_col)]
    elif collector == "set":
        return [Token(TokenType.DELIMITER, "{", ref_line, ref_col)] + inner + [Token(TokenType.DELIMITER, "}", ref_line, ref_col)]
    elif collector in ("tuple", "sum", "any", "all", "min", "max"):
        return [
            Token(TokenType.IDENTIFIER, collector, ref_line, ref_col),
            Token(TokenType.DELIMITER, "(", ref_line, ref_col)
        ] + inner + [Token(TokenType.DELIMITER, ")", ref_line, ref_col)]
    else:
        return [Token(TokenType.DELIMITER, "(", ref_line, ref_col)] + inner + [Token(TokenType.DELIMITER, ")", ref_line, ref_col)]


def extract_pipeline_target(tokens: list[Token], start_idx: int) -> tuple[list[Token], int]:
    """Extracts the callable on the right of |>."""
    operand: list[Token] = []
    i = start_idx
    n = len(tokens)
    paren_depth = 0
    bracket_depth = 0

    while i < n:
        tok = tokens[i]

        if tok.value == "(":
            paren_depth += 1
        elif tok.value == ")":
            if paren_depth == 0:
                break
            paren_depth -= 1
        elif tok.value == "[":
            bracket_depth += 1
        elif tok.value == "]":
            if bracket_depth == 0:
                break
            bracket_depth -= 1

        if paren_depth == 0 and bracket_depth == 0:
            if tok.type == TokenType.PIPE:
                break
            if tok.type in (TokenType.NEWLINE, TokenType.EOF):
                break
            if tok.type in (TokenType.OP, TokenType.DELIMITER) and tok.value in (",", ";", ":"):
                break

        operand.append(tok)
        i += 1

        if paren_depth == 0 and bracket_depth == 0:
            if operand and operand[-1].value == ")":
                break

    return operand, i


def build_pipeline_call(left: list[Token], right: list[Token], pipe_tok: Token) -> list[Token]:
    """Builds lowered call: func(left) or func(left, a) or func(a, left, b)."""
    line = pipe_tok.line
    col = pipe_tok.col

    if right and right[-1].value == ")":
        depth = 0
        open_idx = -1
        for idx in range(len(right) - 1, -1, -1):
            if right[idx].value == ")":
                depth += 1
            elif right[idx].value == "(":
                depth -= 1
                if depth == 0:
                    open_idx = idx
                    break

        if open_idx > 0:
            func_parts = right[:open_idx]
            args_parts = right[open_idx + 1:-1]

            placeholder_idx = -1
            for a_idx, a_tok in enumerate(args_parts):
                if a_tok.type == TokenType.IDENTIFIER and a_tok.value == "_":
                    placeholder_idx = a_idx
                    break

            call_tokens: list[Token] = []
            call_tokens.extend(func_parts)
            call_tokens.append(Token(TokenType.DELIMITER, "(", line, col))

            if placeholder_idx != -1:
                call_tokens.extend(args_parts[:placeholder_idx])
                call_tokens.extend(left)
                call_tokens.extend(args_parts[placeholder_idx + 1:])
            else:
                call_tokens.extend(left)
                if args_parts:
                    call_tokens.append(Token(TokenType.DELIMITER, ",", line, col))
                    call_tokens.extend(args_parts)

            call_tokens.append(Token(TokenType.DELIMITER, ")", line, col))
            return call_tokens

    call_tokens = []
    is_complex = any(t.value == "lambda" for t in right)
    already_parenthesized = right and right[0].value == "(" and right[-1].value == ")"
    if is_complex and not already_parenthesized:
        call_tokens.append(Token(TokenType.DELIMITER, "(", line, col))
    call_tokens.extend(right)
    if is_complex and not already_parenthesized:
        call_tokens.append(Token(TokenType.DELIMITER, ")", line, col))
    call_tokens.append(Token(TokenType.DELIMITER, "(", line, col))
    call_tokens.extend(left)
    call_tokens.append(Token(TokenType.DELIMITER, ")", line, col))
    return call_tokens


def try_fuse_pipeline_steps(
    curr_left: list[Token],
    steps: list[tuple[Token, list[Token]]],
    var_counter_fn: Optional[Callable[[], int]] = None,
) -> tuple[Optional[list[Token]], int]:
    """Attempts to fuse a sequence of steps starting at steps[0]."""
    step_idx = 0
    num_steps = len(steps)

    # 1. Collect leading filters
    filter_preds: list[list[Token]] = []
    while step_idx < num_steps:
        pred = parse_filter_step(steps[step_idx][1])
        if pred is None:
            break
        filter_preds.append(pred)
        step_idx += 1

    # 2. Collect maps
    map_funcs: list[list[Token]] = []
    while step_idx < num_steps:
        fn = parse_map_step(steps[step_idx][1])
        if fn is None:
            break
        map_funcs.append(fn)
        step_idx += 1

    # 3. Collect collector
    collector: Optional[str] = None
    if step_idx < num_steps:
        col = is_collector_step(steps[step_idx][1])
        if col is not None:
            collector = col
            step_idx += 1

    # Check if fusible
    is_fusible = False
    if collector is not None and (len(filter_preds) > 0 or len(map_funcs) > 0):
        is_fusible = True
    elif len(filter_preds) > 0 and len(map_funcs) > 0:
        is_fusible = True
    elif len(filter_preds) >= 2:
        is_fusible = True

    if not is_fusible or step_idx == 0:
        return None, 0

    ref_line = steps[0][0].line
    ref_col = steps[0][0].col
    fused = build_fused_comprehension(
        curr_left=curr_left,
        filter_preds=filter_preds,
        map_funcs=map_funcs,
        collector=collector,
        ref_line=ref_line,
        ref_col=ref_col,
        var_counter_fn=var_counter_fn,
    )
    return fused, step_idx


def process_pipeline_chain(
    left_tokens: list[Token],
    pipe_steps: list[tuple[Token, list[Token]]],
    add_explanation: Optional[Callable[[int, str], None]] = None,
    var_counter_fn: Optional[Callable[[], int]] = None,
) -> list[Token]:
    """Processes a chain of pipeline steps, detecting and fusing map/filter/collector chains."""
    step_i = 0
    num_steps = len(pipe_steps)
    curr_left = left_tokens

    while step_i < num_steps:
        fused, consumed_steps = try_fuse_pipeline_steps(curr_left, pipe_steps[step_i:], var_counter_fn=var_counter_fn)
        if fused is not None and consumed_steps > 0:
            if add_explanation:
                add_explanation(pipe_steps[step_i][0].line, "pipeline fused → Python list comprehension")
            curr_left = fused
            step_i += consumed_steps
        else:
            pipe_tok, right_tokens = pipe_steps[step_i]
            if add_explanation:
                add_explanation(pipe_tok.line, "pipeline step → direct function call")
            curr_left = build_pipeline_call(curr_left, right_tokens, pipe_tok)
            step_i += 1

    return curr_left


def transform_pipelines(
    tokens: list[Token],
    filename: str = "<string>",
    add_explanation: Optional[Callable[[int, str], None]] = None,
    var_counter_fn: Optional[Callable[[], int]] = None,
) -> list[Token]:
    """
    Transforms pipeline tokens:
    - `data |> func` into `func(data)`
    - `data |> func(a, b)` into `func(data, a, b)`
    - `data |> func(a, _, b)` into `func(a, data, b)`
    - Fuses chains like `data |> filter(...) |> map(...) |> list` into
      direct list comprehensions `[map(x) for x in data if filter(x)]`.
    """
    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.PIPE:
            while result and result[-1].type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                result.pop()
            left_tokens = extract_left_operand(result)
            if not left_tokens:
                raise RadicalSyntaxError(
                    message="Missing input expression before '|>'",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )

            pipe_steps: list[tuple[Token, list[Token]]] = []
            curr_i = i

            while curr_i < n and tokens[curr_i].type == TokenType.PIPE:
                pipe_tok = tokens[curr_i]
                curr_i += 1
                while curr_i < n and tokens[curr_i].type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                    curr_i += 1

                right_tokens, next_i = extract_pipeline_target(tokens, curr_i)
                if not right_tokens:
                    raise RadicalSyntaxError(
                        message="Missing target function after '|>'",
                        filename=filename,
                        lineno=pipe_tok.line,
                        col_offset=pipe_tok.col,
                    )
                pipe_steps.append((pipe_tok, right_tokens))
                curr_i = next_i

                peek_i = curr_i
                while peek_i < n and tokens[peek_i].type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                    peek_i += 1
                if peek_i < n and tokens[peek_i].type == TokenType.PIPE:
                    curr_i = peek_i
                else:
                    break

            lowered_chain = process_pipeline_chain(
                left_tokens,
                pipe_steps,
                add_explanation=add_explanation,
                var_counter_fn=var_counter_fn,
            )
            result.extend(lowered_chain)
            i = curr_i
            continue

        result.append(tok)
        i += 1

    return result
