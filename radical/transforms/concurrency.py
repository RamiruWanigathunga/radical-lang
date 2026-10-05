"""
Radical Language Transforms: Concurrency & Hardware Acceleration.
Transforms Cartesian matrix loops (x), multi-core CPU parallel loops (`parallel for`),
and zero-CUDA Apple Silicon Metal/SIMD GPU compute loops (`gpu for`).
"""

from typing import Callable, Optional
from radical.token import Token, TokenType
from radical.exceptions import RadicalSyntaxError


def transform_cartesian_loops(tokens: list[Token]) -> tuple[list[Token], bool]:
    """
    Transforms Cartesian loops `for x, y in (A x B):` into
    `for x, y in itertools.product(A, B):`.
    Supports arbitrary N-dimensional products (A x B x C ...).
    Returns transformed tokens and a boolean indicating whether itertools import is required.
    """
    result: list[Token] = []
    requires_itertools = False
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.IDENTIFIER and tok.value == "in" and i + 1 < n and tokens[i + 1].value == "(":
            open_paren_idx = i + 1
            close_paren_idx = -1
            depth = 0
            has_cartesian_x = False

            for j in range(open_paren_idx, n):
                curr = tokens[j]
                if curr.value == "(":
                    depth += 1
                elif curr.value == ")":
                    depth -= 1
                    if depth == 0:
                        close_paren_idx = j
                        break
                elif depth == 1 and curr.value == "x" and curr.type in (TokenType.IDENTIFIER, TokenType.CARTESIAN_X):
                    has_cartesian_x = True

            if has_cartesian_x and close_paren_idx != -1:
                requires_itertools = True
                result.append(tok)
                inner_tokens = tokens[open_paren_idx + 1:close_paren_idx]
                groups: list[list[Token]] = []
                curr_group: list[Token] = []
                d = 0
                for t in inner_tokens:
                    if t.value in ("(", "[", "{"):
                        d += 1
                    elif t.value in (")", "]", "}"):
                        d -= 1
                    if d == 0 and t.value == "x":
                        if curr_group:
                            groups.append(curr_group)
                            curr_group = []
                        continue
                    curr_group.append(t)
                if curr_group:
                    groups.append(curr_group)

                ref_tok = tokens[open_paren_idx]
                product_tokens: list[Token] = [
                    Token(TokenType.IDENTIFIER, "itertools", ref_tok.line, ref_tok.col),
                    Token(TokenType.OP, ".", ref_tok.line, ref_tok.col),
                    Token(TokenType.IDENTIFIER, "product", ref_tok.line, ref_tok.col),
                    Token(TokenType.DELIMITER, "(", ref_tok.line, ref_tok.col),
                ]
                for g_idx, group in enumerate(groups):
                    product_tokens.extend(group)
                    if g_idx < len(groups) - 1:
                        product_tokens.append(Token(TokenType.DELIMITER, ",", ref_tok.line, ref_tok.col))
                product_tokens.append(Token(TokenType.DELIMITER, ")", ref_tok.line, ref_tok.col))

                result.extend(product_tokens)
                i = close_paren_idx + 1
                continue

        result.append(tok)
        i += 1

    return result, requires_itertools


def transform_parallel_loops(
    tokens: list[Token],
    filename: str = "<string>",
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms `parallel for item in items:` or `parallel(threads=4) for item in items:`
    into multithreaded worker dispatch using `_rad_parallel_for`.
    """
    has_parallel = any(t.type == TokenType.KW_PARALLEL for t in tokens)
    if not has_parallel:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)
    worker_id = 0

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.KW_PARALLEL:
            assign_tokens: list[Token] = []
            if result and result[-1].value == "=":
                result.pop()  # pop '='
                while result and result[-1].type not in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                    assign_tokens.insert(0, result.pop())

            worker_id += 1
            worker_fn_name = f"_rad_par_worker_{worker_id}"
            ref_line = tok.line
            ref_col = assign_tokens[0].col if assign_tokens else tok.col
            if add_explanation is not None:
                add_explanation(ref_line, "parallel loop → process/thread pool (auto workers)")
            i += 1

            # Check for parallel list comprehension: parallel [ expr for target in iter ]
            if i < n and tokens[i].value == "[":
                i += 1  # skip '['
                expr_tokens: list[Token] = []
                paren_depth = bracket_depth = brace_depth = 0
                while i < n:
                    curr = tokens[i]
                    if curr.value in ("(", "[", "{"):
                        if curr.value == "(": paren_depth += 1
                        elif curr.value == "[": bracket_depth += 1
                        elif curr.value == "{": brace_depth += 1
                    elif curr.value in (")", "]", "}"):
                        if curr.value == ")": paren_depth -= 1
                        elif curr.value == "]": bracket_depth -= 1
                        elif curr.value == "}": brace_depth -= 1
                    if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0 and curr.value == "for":
                        i += 1  # skip 'for'
                        break
                    expr_tokens.append(curr)
                    i += 1

                target_tokens: list[Token] = []
                while i < n and tokens[i].value != "in":
                    target_tokens.append(tokens[i])
                    i += 1
                if i < n and tokens[i].value == "in":
                    i += 1  # skip 'in'

                iter_tokens: list[Token] = []
                paren_depth = bracket_depth = brace_depth = 0
                while i < n:
                    curr = tokens[i]
                    if curr.value in ("(", "[", "{"):
                        if curr.value == "(": paren_depth += 1
                        elif curr.value == "[": bracket_depth += 1
                        elif curr.value == "{": brace_depth += 1
                    elif curr.value in (")", "]", "}"):
                        if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0 and curr.value == "]":
                            i += 1  # skip ']'
                            break
                        if curr.value == ")": paren_depth -= 1
                        elif curr.value == "]": bracket_depth -= 1
                        elif curr.value == "}": brace_depth -= 1
                    iter_tokens.append(curr)
                    i += 1

                if assign_tokens:
                    result.extend(assign_tokens)
                    result.append(Token(TokenType.OP, "=", ref_line, ref_col))

                comp_call: list[Token] = [
                    Token(TokenType.IDENTIFIER, "_rad_parallel_for", ref_line, ref_col),
                    Token(TokenType.DELIMITER, "(", ref_line, ref_col),
                ]
                comp_call.extend(iter_tokens)
                comp_call.append(Token(TokenType.DELIMITER, ",", ref_line, ref_col))
                comp_call.append(Token(TokenType.IDENTIFIER, "lambda", ref_line, ref_col))
                comp_call.extend(target_tokens)
                comp_call.append(Token(TokenType.DELIMITER, ":", ref_line, ref_col))
                comp_call.extend(expr_tokens)
                comp_call.append(Token(TokenType.DELIMITER, ",", ref_line, ref_col))
                comp_call.append(Token(TokenType.IDENTIFIER, "mode", ref_line, ref_col))
                comp_call.append(Token(TokenType.OP, "=", ref_line, ref_col))
                comp_call.append(Token(TokenType.STRING, '"process"', ref_line, ref_col))
                comp_call.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))

                result.extend(comp_call)
                continue

            options_tokens: list[Token] = []
            if i < n and tokens[i].value == "(":
                i += 1
                depth = 1
                while i < n and depth > 0:
                    curr = tokens[i]
                    if curr.value == "(":
                        depth += 1
                    elif curr.value == ")":
                        depth -= 1
                        if depth == 0:
                            i += 1
                            break
                    options_tokens.append(curr)
                    i += 1

            if i >= n or tokens[i].value != "for":
                raise RadicalSyntaxError(
                    message="Expected 'for' after 'parallel'",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            i += 1

            target_tokens = []
            while i < n and tokens[i].value != "in":
                target_tokens.append(tokens[i])
                i += 1

            if i >= n or tokens[i].value != "in":
                raise RadicalSyntaxError(
                    message="Expected 'in' in parallel for loop",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            i += 1

            iter_tokens = []
            depth = 0
            while i < n:
                curr = tokens[i]
                if curr.value in ("(", "[", "{"):
                    depth += 1
                elif curr.value in (")", "]", "}"):
                    depth -= 1
                elif curr.value == ":" and depth == 0:
                    i += 1
                    break
                iter_tokens.append(curr)
                i += 1

            body_tokens: list[Token] = []
            while i < n:
                curr = tokens[i]
                if curr.type in (TokenType.INDENT, TokenType.DEDENT):
                    i += 1
                    continue
                if curr.type not in (TokenType.NEWLINE, TokenType.COMMENT, TokenType.EOF):
                    if curr.col <= ref_col:
                        break
                body_tokens.append(curr)
                i += 1

            is_tuple_target = any(t.value == "," for t in target_tokens)
            worker_param = "_rad_item" if is_tuple_target else "".join(t.value for t in target_tokens).strip()

            worker_tokens: list[Token] = [
                Token(TokenType.IDENTIFIER, "def", ref_line, ref_col),
                Token(TokenType.IDENTIFIER, worker_fn_name, ref_line, ref_col),
                Token(TokenType.DELIMITER, "(", ref_line, ref_col),
                Token(TokenType.IDENTIFIER, worker_param, ref_line, ref_col),
                Token(TokenType.DELIMITER, ")", ref_line, ref_col),
                Token(TokenType.DELIMITER, ":", ref_line, ref_col),
                Token(TokenType.NEWLINE, "\n", ref_line, ref_col),
            ]

            if is_tuple_target:
                worker_tokens.append(Token(TokenType.INDENT, "    ", ref_line, ref_col + 4))
                worker_tokens.extend(target_tokens)
                worker_tokens.append(Token(TokenType.OP, "=", ref_line, ref_col + 4))
                worker_tokens.append(Token(TokenType.IDENTIFIER, "_rad_item", ref_line, ref_col + 4))
                worker_tokens.append(Token(TokenType.NEWLINE, "\n", ref_line, ref_col + 4))

            worker_tokens.extend(body_tokens)
            worker_tokens.append(Token(TokenType.NEWLINE, "\n", ref_line, ref_col))

            call_tokens: list[Token] = []
            if assign_tokens:
                call_tokens.extend(assign_tokens)
                call_tokens.append(Token(TokenType.OP, "=", ref_line, ref_col))
            call_tokens.extend([
                Token(TokenType.IDENTIFIER, "_rad_parallel_for", ref_line, ref_col),
                Token(TokenType.DELIMITER, "(", ref_line, ref_col),
            ])
            call_tokens.extend(iter_tokens)
            call_tokens.append(Token(TokenType.DELIMITER, ",", ref_line, ref_col))
            call_tokens.append(Token(TokenType.IDENTIFIER, worker_fn_name, ref_line, ref_col))
            if options_tokens:
                call_tokens.append(Token(TokenType.DELIMITER, ",", ref_line, ref_col))
                call_tokens.extend(options_tokens)
            elif assign_tokens:
                call_tokens.append(Token(TokenType.DELIMITER, ",", ref_line, ref_col))
                call_tokens.append(Token(TokenType.IDENTIFIER, "mode", ref_line, ref_col))
                call_tokens.append(Token(TokenType.OP, "=", ref_line, ref_col))
                call_tokens.append(Token(TokenType.STRING, '"process"', ref_line, ref_col))
            call_tokens.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))
            call_tokens.append(Token(TokenType.NEWLINE, "\n", ref_line, ref_col))

            result.extend(worker_tokens)
            result.extend(call_tokens)
            continue

        result.append(tok)
        i += 1

    return result, True


def transform_gpu_constructs(
    tokens: list[Token],
    filename: str = "<string>",
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms `gpu for i in 0..N:` and `gpu fn ...` into accelerated GPU/Metal compute dispatches.
    """
    has_gpu = any(t.type == TokenType.KW_GPU for t in tokens)
    if not has_gpu:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)
    kernel_id = 0

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.KW_GPU:
            # Only treat as statement keyword if followed by `for` or `fn`
            if i + 1 < n and (tokens[i + 1].value in ("for", "fn") or tokens[i + 1].type == TokenType.KW_FN):
                kernel_id += 1
                ref_line = tok.line
                ref_col = tok.col
                if add_explanation is not None:
                    add_explanation(ref_line, "gpu loop → zero-copy worker dispatch (Apple Metal/CPU fallback)")
                i += 1

                # Check if `gpu fn`
                if i < n and (tokens[i].type == TokenType.KW_FN or tokens[i].value == "fn"):
                    result.append(Token(TokenType.KW_FN, "fn", ref_line, ref_col))
                    i += 1
                    continue

                # Check if `gpu for`
                if i < n and tokens[i].value == "for":
                    i += 1
                var_tokens: list[Token] = []
                while i < n and tokens[i].value != "in":
                    var_tokens.append(tokens[i])
                    i += 1

                if i >= n or tokens[i].value != "in":
                    raise RadicalSyntaxError(
                        message="Expected 'in' in gpu for loop",
                        filename=filename,
                        lineno=ref_line,
                        col_offset=ref_col,
                    )
                i += 1

                range_tokens: list[Token] = []
                depth = 0
                while i < n:
                    curr = tokens[i]
                    if curr.value in ("(", "[", "{"):
                        depth += 1
                    elif curr.value in (")", "]", "}"):
                        depth -= 1
                    elif curr.value == ":" and depth == 0:
                        i += 1
                        break
                    range_tokens.append(curr)
                    i += 1

                body_tokens: list[Token] = []
                while i < n:
                    curr = tokens[i]
                    if curr.type in (TokenType.INDENT, TokenType.DEDENT):
                        i += 1
                        continue
                    if curr.type not in (TokenType.NEWLINE, TokenType.COMMENT, TokenType.EOF):
                        if curr.col <= ref_col:
                            break
                    body_tokens.append(curr)
                    i += 1

                kernel_fn_name = f"_rad_gpu_kernel_{kernel_id}"
                var_name = "".join(t.value for t in var_tokens).strip()

                worker_tokens: list[Token] = [
                    Token(TokenType.IDENTIFIER, "def", ref_line, ref_col),
                    Token(TokenType.IDENTIFIER, kernel_fn_name, ref_line, ref_col),
                    Token(TokenType.DELIMITER, "(", ref_line, ref_col),
                    Token(TokenType.IDENTIFIER, var_name, ref_line, ref_col),
                    Token(TokenType.DELIMITER, ")", ref_line, ref_col),
                    Token(TokenType.DELIMITER, ":", ref_line, ref_col),
                    Token(TokenType.NEWLINE, "\n", ref_line, ref_col),
                ]
                worker_tokens.extend(body_tokens)
                worker_tokens.append(Token(TokenType.NEWLINE, "\n", ref_line, ref_col))

                call_tokens: list[Token] = [
                    Token(TokenType.IDENTIFIER, "gpu", ref_line, ref_col),
                    Token(TokenType.OP, ".", ref_line, ref_col),
                    Token(TokenType.IDENTIFIER, "execute_loop", ref_line, ref_col),
                    Token(TokenType.DELIMITER, "(", ref_line, ref_col),
                    Token(TokenType.IDENTIFIER, "len", ref_line, ref_col),
                    Token(TokenType.DELIMITER, "(", ref_line, ref_col),
                ]
                call_tokens.extend(range_tokens)
                call_tokens.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))
                call_tokens.append(Token(TokenType.DELIMITER, ",", ref_line, ref_col))
                call_tokens.append(Token(TokenType.IDENTIFIER, kernel_fn_name, ref_line, ref_col))
                call_tokens.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))
                call_tokens.append(Token(TokenType.NEWLINE, "\n", ref_line, ref_col))

                result.extend(worker_tokens)
                result.extend(call_tokens)
                continue

        result.append(tok)
        i += 1

    return result, True
