"""
Radical Language Transforms: Control Flow & Scoped Blocks.
Transforms `using` deterministic resource blocks, `unsafe:` pointer blocks,
`defer` LIFO cleanup stacks, and `select:` concurrency multiplexing.
"""

from typing import Callable, Optional
from radical.token import Token, TokenType


def transform_using(
    tokens: list[Token],
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms deterministic resource management:
    `using f = open("file"):` -> `with open("file") as f:`
    `using open("file"):` -> `with open("file"):`
    """
    has_using = any(t.type == TokenType.KW_USING for t in tokens)
    if not has_using:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.KW_USING:
            ref_line = tok.line
            ref_col = tok.col
            if add_explanation is not None:
                add_explanation(ref_line, "using resource block → deterministic context manager")
            i += 1
            stmt_tokens: list[Token] = []
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
                stmt_tokens.append(curr)
                i += 1

            eq_idx = -1
            cur_depth = 0
            for idx, t in enumerate(stmt_tokens):
                if t.value in ("(", "[", "{"):
                    cur_depth += 1
                elif t.value in (")", "]", "}"):
                    cur_depth -= 1
                elif cur_depth == 0 and t.value == "=" and t.type == TokenType.OP:
                    eq_idx = idx
                    break

            result.append(Token(TokenType.IDENTIFIER, "with", ref_line, ref_col))
            if eq_idx != -1:
                var_tokens = stmt_tokens[:eq_idx]
                expr_tokens = stmt_tokens[eq_idx + 1:]
                result.extend(expr_tokens)
                result.append(Token(TokenType.IDENTIFIER, "as", ref_line, ref_col))
                result.extend(var_tokens)
            else:
                result.extend(stmt_tokens)
            result.append(Token(TokenType.DELIMITER, ":", ref_line, ref_col))
            continue

        result.append(tok)
        i += 1
    return result, True


def transform_unsafe(
    tokens: list[Token],
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms `unsafe:` scoped blocks into `with _rad_unsafe_context():`
    """
    has_unsafe = any(t.type == TokenType.KW_UNSAFE for t in tokens)
    if not has_unsafe:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.KW_UNSAFE:
            ref_line = tok.line
            ref_col = tok.col
            if add_explanation is not None:
                add_explanation(ref_line, "unsafe block → scoped unchecked raw pointer access")
            i += 1
            if i < n and tokens[i].value == ":":
                i += 1
            result.append(Token(TokenType.IDENTIFIER, "with", ref_line, ref_col))
            result.append(Token(TokenType.IDENTIFIER, "_rad_unsafe_context", ref_line, ref_col))
            result.append(Token(TokenType.DELIMITER, "(", ref_line, ref_col))
            result.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))
            result.append(Token(TokenType.DELIMITER, ":", ref_line, ref_col))
            continue

        result.append(tok)
        i += 1
    return result, True


def wrap_function_with_defer(body_tokens: list[Token], inner_indent: int) -> list[Token]:
    """Wraps function body tokens in `with _RadicalDeferStack() as _rad_defer:`."""
    res: list[Token] = []
    ref_line = body_tokens[0].line if body_tokens else 1
    res.append(Token(TokenType.NEWLINE, "\n", ref_line, 0))
    res.append(Token(TokenType.IDENTIFIER, "with", ref_line, inner_indent - 4 if inner_indent > 4 else 4))
    res.append(Token(TokenType.IDENTIFIER, "_RadicalDeferStack", ref_line, inner_indent))
    res.append(Token(TokenType.DELIMITER, "(", ref_line, inner_indent))
    res.append(Token(TokenType.DELIMITER, ")", ref_line, inner_indent))
    res.append(Token(TokenType.IDENTIFIER, "as", ref_line, inner_indent))
    res.append(Token(TokenType.IDENTIFIER, "_rad_defer", ref_line, inner_indent))
    res.append(Token(TokenType.DELIMITER, ":", ref_line, inner_indent))
    res.append(Token(TokenType.NEWLINE, "\n", ref_line, 0))

    j = 0
    m = len(body_tokens)
    at_line_start = True

    while j < m:
        b_tok = body_tokens[j]

        if b_tok.type in (TokenType.INDENT, TokenType.DEDENT):
            j += 1
            continue

        if b_tok.type == TokenType.NEWLINE:
            res.append(b_tok)
            at_line_start = True
            j += 1
            continue

        new_col = b_tok.col + 4 if at_line_start else b_tok.col
        at_line_start = False

        if b_tok.type == TokenType.KW_DEFER:
            j += 1
            defer_stmt_tokens: list[Token] = []
            while j < m and body_tokens[j].type not in (TokenType.NEWLINE, TokenType.EOF):
                defer_stmt_tokens.append(body_tokens[j])
                j += 1

            res.append(Token(TokenType.IDENTIFIER, "_rad_defer", b_tok.line, new_col))
            res.append(Token(TokenType.OP, ".", b_tok.line, new_col))
            res.append(Token(TokenType.IDENTIFIER, "defer", b_tok.line, new_col))
            res.append(Token(TokenType.DELIMITER, "(", b_tok.line, new_col))
            res.append(Token(TokenType.IDENTIFIER, "lambda", b_tok.line, new_col))
            res.append(Token(TokenType.DELIMITER, ":", b_tok.line, new_col))
            res.extend(defer_stmt_tokens)
            res.append(Token(TokenType.DELIMITER, ")", b_tok.line, new_col))
            continue

        res.append(Token(b_tok.type, b_tok.value, b_tok.line, new_col, b_tok.end_line, b_tok.end_col + 4))
        j += 1

    return res


def transform_defer(tokens: list[Token]) -> tuple[list[Token], bool]:
    """
    Transforms `defer <stmt>` into LIFO deferred actions using `_RadicalDeferStack`.
    Inside functions, wraps the function body with `with _RadicalDeferStack() as _rad_defer:`
    and replaces `defer <stmt>` with `_rad_defer.defer(lambda: <stmt>)`.
    Returns transformed tokens and a boolean indicating whether defer runtime is required.
    """
    has_defer = any(t.type == TokenType.KW_DEFER for t in tokens)
    if not has_defer:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.IDENTIFIER and tok.value in ("def", "async") and (
            tok.value == "def" or (i + 1 < n and tokens[i + 1].value == "def")
        ):
            header_tokens: list[Token] = []
            while i < n and tokens[i].value != ":":
                header_tokens.append(tokens[i])
                i += 1
            if i < n:
                header_tokens.append(tokens[i])  # ':'
                i += 1

            fn_indent = tok.col
            body_tokens: list[Token] = []
            while i < n:
                curr = tokens[i]
                if curr.type not in (TokenType.NEWLINE, TokenType.COMMENT, TokenType.EOF):
                    if curr.col <= fn_indent and not (curr.type in (TokenType.INDENT, TokenType.DEDENT)):
                        break
                body_tokens.append(curr)
                i += 1

            fn_has_defer = any(t.type == TokenType.KW_DEFER for t in body_tokens)
            if fn_has_defer:
                transformed_body = wrap_function_with_defer(body_tokens, fn_indent + 4)
                result.extend(header_tokens)
                result.extend(transformed_body)
            else:
                result.extend(header_tokens)
                result.extend(body_tokens)
            continue

        result.append(tok)
        i += 1

    return result, True


def transform_select(
    tokens: list[Token],
    add_explanation: Optional[Callable[[int, str], None]] = None,
    var_counter_fn: Optional[Callable[[], int]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms Go-style `select:` channel multiplexing blocks into non-blocking polling logic.
    """
    has_select = any(t.type == TokenType.KW_SELECT for t in tokens)
    if not has_select:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)
    local_counter = 0

    def next_counter() -> int:
        nonlocal local_counter
        if var_counter_fn is not None:
            return var_counter_fn()
        local_counter += 1
        return local_counter

    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.KW_SELECT:
            if add_explanation is not None:
                add_explanation(tok.line, "select block → non-blocking channel polling")
            sel_line = tok.line
            sel_col = tok.col
            i += 1
            if i < n and tokens[i].value == ":":
                i += 1

            while i < n and tokens[i].type in (TokenType.NEWLINE, TokenType.INDENT):
                i += 1

            cases: list[tuple[str, Optional[str], Optional[list[Token]], list[Token]]] = []

            while i < n:
                curr = tokens[i]
                if curr.type == TokenType.DEDENT:
                    i += 1
                    break
                if curr.col <= sel_col and curr.type not in (TokenType.NEWLINE, TokenType.COMMENT):
                    break
                if curr.type in (TokenType.NEWLINE, TokenType.COMMENT):
                    i += 1
                    continue

                # Check for 'case default:' or 'default:'
                is_default = (curr.value == "default") or (curr.value == "case" and i + 1 < n and tokens[i + 1].value == "default")
                if is_default:
                    while i < n and tokens[i].value != ":":
                        i += 1
                    if i < n and tokens[i].value == ":":
                        i += 1
                    case_body: list[Token] = []
                    depth = 0
                    while i < n:
                        if tokens[i].type == TokenType.INDENT:
                            depth += 1
                        elif tokens[i].type == TokenType.DEDENT:
                            if depth > 0:
                                depth -= 1
                                if depth == 0:
                                    i += 1
                                    break
                            else:
                                break
                        case_body.append(tokens[i])
                        i += 1
                    cases.append(("default", None, None, case_body))
                    continue

                if curr.value == "case":
                    i += 1
                    header_tokens: list[Token] = []
                    while i < n and tokens[i].value != ":":
                        header_tokens.append(tokens[i])
                        i += 1
                    if i < n and tokens[i].value == ":":
                        i += 1

                    case_body = []
                    depth = 0
                    while i < n:
                        if tokens[i].type == TokenType.INDENT:
                            depth += 1
                        elif tokens[i].type == TokenType.DEDENT:
                            if depth > 0:
                                depth -= 1
                                if depth == 0:
                                    i += 1
                                    break
                            else:
                                break
                        case_body.append(tokens[i])
                        i += 1

                    var_name = None
                    eq_idx = -1
                    for h_i, h_tok in enumerate(header_tokens):
                        if h_tok.value == "=":
                            eq_idx = h_i
                            break

                    if eq_idx != -1:
                        var_name = header_tokens[0].value
                        call_tokens = header_tokens[eq_idx + 1:]
                    else:
                        call_tokens = header_tokens

                    # Extract chan before .recv()
                    recv_idx = -1
                    for c_i, c_tok in enumerate(call_tokens):
                        if c_tok.value == "recv":
                            recv_idx = c_i
                            break

                    if recv_idx > 0 and call_tokens[recv_idx - 1].value == ".":
                        chan_toks = call_tokens[:recv_idx - 1]
                    else:
                        chan_toks = call_tokens

                    cases.append(("recv", var_name, chan_toks, case_body))
                    continue

                i += 1

            cid = next_counter()
            sel_flag = f"_rad_sel_{cid}"
            emitted: list[Token] = [
                Token(TokenType.IDENTIFIER, sel_flag, sel_line, sel_col),
                Token(TokenType.OP, "=", sel_line, sel_col),
                Token(TokenType.IDENTIFIER, "False", sel_line, sel_col),
                Token(TokenType.NEWLINE, "\n", sel_line, sel_col),
            ]

            for kind, vname, c_toks, c_body in cases:
                if kind == "recv":
                    cid_ok = next_counter()
                    cid_tmp = next_counter()
                    ok_var = f"_rad_ok_{cid_ok}"
                    tmp_var = f"_rad_tmp_{cid_tmp}"

                    emitted.extend([
                        Token(TokenType.IDENTIFIER, "if", sel_line, sel_col),
                        Token(TokenType.IDENTIFIER, "not", sel_line, sel_col),
                        Token(TokenType.IDENTIFIER, sel_flag, sel_line, sel_col),
                        Token(TokenType.DELIMITER, ":", sel_line, sel_col),
                        Token(TokenType.NEWLINE, "\n", sel_line, sel_col),
                        Token(TokenType.IDENTIFIER, "    " + ok_var, sel_line, sel_col + 4),
                        Token(TokenType.DELIMITER, ",", sel_line, sel_col + 4),
                        Token(TokenType.IDENTIFIER, tmp_var, sel_line, sel_col + 4),
                        Token(TokenType.OP, "=", sel_line, sel_col + 4),
                    ])
                    if c_toks:
                        emitted.extend(c_toks)
                    else:
                        emitted.append(Token(TokenType.IDENTIFIER, "ch", sel_line, sel_col + 4))
                    emitted.extend([
                        Token(TokenType.OP, ".", sel_line, sel_col + 4),
                        Token(TokenType.IDENTIFIER, "try_recv", sel_line, sel_col + 4),
                        Token(TokenType.DELIMITER, "(", sel_line, sel_col + 4),
                        Token(TokenType.DELIMITER, ")", sel_line, sel_col + 4),
                        Token(TokenType.NEWLINE, "\n", sel_line, sel_col),
                        Token(TokenType.IDENTIFIER, "    if", sel_line, sel_col + 4),
                        Token(TokenType.IDENTIFIER, ok_var, sel_line, sel_col + 4),
                        Token(TokenType.DELIMITER, ":", sel_line, sel_col + 4),
                        Token(TokenType.NEWLINE, "\n", sel_line, sel_col),
                    ])
                    if vname:
                        emitted.extend([
                            Token(TokenType.IDENTIFIER, "        " + vname, sel_line, sel_col + 8),
                            Token(TokenType.OP, "=", sel_line, sel_col + 8),
                            Token(TokenType.IDENTIFIER, tmp_var, sel_line, sel_col + 8),
                            Token(TokenType.NEWLINE, "\n", sel_line, sel_col),
                        ])
                    emitted.extend([
                        Token(TokenType.IDENTIFIER, "        " + sel_flag, sel_line, sel_col + 8),
                        Token(TokenType.OP, "=", sel_line, sel_col + 8),
                        Token(TokenType.IDENTIFIER, "True", sel_line, sel_col + 8),
                        Token(TokenType.NEWLINE, "\n", sel_line, sel_col),
                    ])
                    at_start = True
                    for b_tok in c_body:
                        if b_tok.type in (TokenType.INDENT, TokenType.DEDENT):
                            continue
                        if b_tok.type == TokenType.NEWLINE:
                            emitted.append(b_tok)
                            at_start = True
                        else:
                            col = (sel_col + 8) if at_start else b_tok.col
                            emitted.append(Token(b_tok.type, b_tok.value, b_tok.line, col))
                            at_start = False
                elif kind == "default":
                    emitted.extend([
                        Token(TokenType.IDENTIFIER, "if", sel_line, sel_col),
                        Token(TokenType.IDENTIFIER, "not", sel_line, sel_col),
                        Token(TokenType.IDENTIFIER, sel_flag, sel_line, sel_col),
                        Token(TokenType.DELIMITER, ":", sel_line, sel_col),
                        Token(TokenType.NEWLINE, "\n", sel_line, sel_col),
                    ])
                    at_start = True
                    for b_tok in c_body:
                        if b_tok.type in (TokenType.INDENT, TokenType.DEDENT):
                            continue
                        if b_tok.type == TokenType.NEWLINE:
                            emitted.append(b_tok)
                            at_start = True
                        else:
                            col = (sel_col + 4) if at_start else b_tok.col
                            emitted.append(Token(b_tok.type, b_tok.value, b_tok.line, col))
                            at_start = False
                    emitted.append(Token(TokenType.NEWLINE, "\n", sel_line, sel_col))

            result.extend(emitted)
            continue

        result.append(tok)
        i += 1

    return result, True
