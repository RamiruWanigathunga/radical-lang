"""
Operator, expression, and template transformations for Radical.
"""

from typing import Optional, Callable
from radical.lexer import Token, TokenType
from radical.exceptions import RadicalSyntaxError


def extract_left_operand(tokens: list[Token]) -> list[Token]:
    """Scans backwards to extract the operand immediately preceding a binary operator."""
    if not tokens:
        return []

    operand: list[Token] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    while tokens:
        tok = tokens[-1]
        if tok.value == ")":
            paren_depth += 1
        elif tok.value == "(":
            if paren_depth == 0:
                break
            paren_depth -= 1
        elif tok.value == "]":
            bracket_depth += 1
        elif tok.value == "[":
            if bracket_depth == 0:
                break
            bracket_depth -= 1
        elif tok.value == "}":
            brace_depth += 1
        elif tok.value == "{":
            if brace_depth == 0:
                break
            brace_depth -= 1

        if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            if tok.value in (",", ";", "=", ":", "in", "and", "or", "|>", "for", "return", "if", "else"):
                break
            if tok.type in (TokenType.NEWLINE, TokenType.INDENT, TokenType.DEDENT):
                break

        operand.insert(0, tokens.pop())

        if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            # If we've collected an identifier or number or closed paren/bracket, check if preceded by an op
            if tokens and tokens[-1].type in (TokenType.IDENTIFIER, TokenType.NUMBER) and not (
                operand and operand[0].value in (".", "(", "+", "-", "*", "/", "%", "**", "//")
            ):
                break

    return operand


def extract_right_operand(tokens: list[Token], start_idx: int) -> tuple[list[Token], int]:
    """Scans forward to extract the operand immediately following a binary operator."""
    operand: list[Token] = []
    i = start_idx
    n = len(tokens)
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    while i < n:
        tok = tokens[i]
        if tok.value in ("(", "[", "{"):
            if tok.value == "(":
                paren_depth += 1
            elif tok.value == "[":
                bracket_depth += 1
            elif tok.value == "{":
                brace_depth += 1
        elif tok.value in (")", "]", "}"):
            if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
                break
            if tok.value == ")":
                paren_depth -= 1
            elif tok.value == "]":
                bracket_depth -= 1
            elif tok.value == "}":
                brace_depth -= 1

        if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            # Stop at low-precedence delimiters
            if tok.type in (TokenType.OP, TokenType.DELIMITER) and tok.value in (",", ";", ":", ")", "]", "}", "x", "|>"):
                break
            if tok.type in (TokenType.RANGE_EXCLUSIVE, TokenType.RANGE_INCLUSIVE):
                break
            if tok.type in (TokenType.NEWLINE, TokenType.EOF):
                break
            if tok.value in ("and", "or", "in", "if", "else"):
                break

        operand.append(tok)
        i += 1

        # If we completed a primary or binary expression
        if paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            if tok.value in ("+", "-", "*", "/", "%", "**", "//"):
                continue
            if i < n and tokens[i].value not in (".", "(", "[", "+", "-", "*", "/", "%", "**", "//"):
                break

    return operand, i


def build_range_tokens(
    left_tokens: list[Token],
    right_tokens: list[Token],
    step_tokens: Optional[list[Token]],
    inclusive: bool,
    ref_tok: Token,
) -> list[Token]:
    line = ref_tok.line
    col = ref_tok.col

    # range(start, end) or range(start, (end) + 1)
    res: list[Token] = [
        Token(TokenType.IDENTIFIER, "range", line, col),
        Token(TokenType.DELIMITER, "(", line, col),
    ]
    res.extend(left_tokens)
    res.append(Token(TokenType.DELIMITER, ",", line, col))

    if inclusive:
        res.append(Token(TokenType.DELIMITER, "(", line, col))
        res.extend(right_tokens)
        res.append(Token(TokenType.DELIMITER, ")", line, col))
        res.append(Token(TokenType.OP, "+", line, col))
        res.append(Token(TokenType.NUMBER, "1", line, col))
    else:
        res.extend(right_tokens)

    if step_tokens:
        res.append(Token(TokenType.DELIMITER, ",", line, col))
        res.extend(step_tokens)

    res.append(Token(TokenType.DELIMITER, ")", line, col))
    return res


def transform_tagged_templates(
    tokens: list[Token],
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms tagged template literals:
    `sql"SELECT * FROM users WHERE id = {user_id}"`
    into: `sql(f"SELECT * FROM users WHERE id = {user_id}")`.
    """
    standard_prefixes = {"f", "r", "b", "u", "fr", "rf", "br", "rb"}
    result: list[Token] = []
    i = 0
    n = len(tokens)
    has_tagged = False

    while i < n:
        tok = tokens[i]
        if (tok.type == TokenType.IDENTIFIER and
            i + 1 < n and tokens[i + 1].type == TokenType.STRING and
            tok.end_line == tokens[i + 1].line and tok.end_col == tokens[i + 1].col and
            tok.value.lower() not in standard_prefixes):
            has_tagged = True
            str_tok = tokens[i + 1]
            if add_explanation:
                add_explanation(tok.line, f"tagged template literal: {tok.value}\" \" → {tok.value}(f\"...\")")

            raw_str = str_tok.value
            f_str = raw_str if raw_str.startswith(("f\"", "f'", "f'''", "f\"\"\"")) else f"f{raw_str}"

            result.append(tok)
            result.append(Token(TokenType.DELIMITER, "(", tok.line, tok.end_col))
            result.append(Token(TokenType.STRING, f_str, str_tok.line, str_tok.col, str_tok.end_line, str_tok.end_col))
            result.append(Token(TokenType.DELIMITER, ")", str_tok.end_line, str_tok.end_col))
            i += 2
            continue

        result.append(tok)
        i += 1

    return result, has_tagged


def transform_struct_with(
    tokens: list[Token],
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms immutable copy-update:
    `<expr> with { a: 1, b: 2 }` -> `_rad_copy_with(<expr>, a=1, b=2)`
    """
    result: list[Token] = []
    has_copy_with = False
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.IDENTIFIER and tok.value == "with" and i + 1 < n and tokens[i + 1].value == "{" and len(result) > 0:
            prev = result[-1]
            if prev.type in (TokenType.IDENTIFIER, TokenType.NUMBER) or prev.value in (")", "]"):
                has_copy_with = True
                if add_explanation:
                    add_explanation(tok.line, "copy-update with → functional immutable struct replace")
                i += 2

                expr_tokens: list[Token] = []
                depth = 0
                while result:
                    t = result.pop()
                    if t.value in (")", "]", "}"):
                        depth += 1
                    elif t.value in ("(", "[", "{"):
                        depth -= 1

                    expr_tokens.insert(0, t)
                    if depth <= 0 and (not result or result[-1].value in ("=", ",", "+", "-", "*", "/", "(", "[", "\n") or result[-1].type == TokenType.NEWLINE):
                        break

                brace_tokens: list[Token] = []
                brace_depth = 1
                while i < n and brace_depth > 0:
                    curr = tokens[i]
                    if curr.value == "{":
                        brace_depth += 1
                    elif curr.value == "}":
                        brace_depth -= 1
                        if brace_depth == 0:
                            i += 1
                            break
                    brace_tokens.append(curr)
                    i += 1

                arg_tokens: list[Token] = []
                for bt in brace_tokens:
                    if bt.value == ":":
                        arg_tokens.append(Token(TokenType.OP, "=", bt.line, bt.col))
                    else:
                        arg_tokens.append(bt)

                result.append(Token(TokenType.IDENTIFIER, "_rad_copy_with", tok.line, tok.col))
                result.append(Token(TokenType.DELIMITER, "(", tok.line, tok.col))
                result.extend(expr_tokens)
                if arg_tokens:
                    result.append(Token(TokenType.DELIMITER, ",", tok.line, tok.col))
                    result.extend(arg_tokens)
                result.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))
                continue

        result.append(tok)
        i += 1

    return result, has_copy_with


def transform_try_operator(
    tokens: list[Token],
    add_explanation: Optional[Callable[[int, str], None]] = None,
    counter_fn: Optional[Callable[[], int]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms the Rust-style `?` operator on statements:
    `let val = expr?` or `return expr?` or `expr?`
    into early-exit error handling guards.
    """
    has_question = any(t.type == TokenType.QUESTION for t in tokens)
    if not has_question:
        return tokens, False

    local_counter = 0

    def next_counter() -> int:
        nonlocal local_counter
        if counter_fn is not None:
            return counter_fn()
        local_counter += 1
        return local_counter

    result: list[Token] = []
    i = 0
    n = len(tokens)

    # Break token stream into statement lines (by NEWLINE at depth 0)
    while i < n:
        stmt: list[Token] = []
        depth = 0
        while i < n:
            tok = tokens[i]
            stmt.append(tok)
            i += 1
            if tok.value in ("(", "[", "{"):
                depth += 1
            elif tok.value in (")", "]", "}"):
                depth -= 1
            elif tok.type == TokenType.NEWLINE and depth <= 0:
                break

        # Separate leading INDENT / DEDENT tokens
        leading_indents: list[Token] = []
        stmt_non_indent: list[Token] = []
        seen_content = False
        for t in stmt:
            if not seen_content and t.type in (TokenType.INDENT, TokenType.DEDENT):
                leading_indents.append(t)
            else:
                seen_content = True
                stmt_non_indent.append(t)

        if not stmt_non_indent:
            result.extend(stmt)
            continue

        # Check if this statement contains a QUESTION token
        has_q = any(t.type == TokenType.QUESTION for t in stmt_non_indent)
        if not has_q:
            result.extend(stmt)
            continue

        # Strip trailing newline/comments to inspect statement body
        newline_tok = None
        if stmt_non_indent and stmt_non_indent[-1].type == TokenType.NEWLINE:
            newline_tok = stmt_non_indent[-1]
            body = stmt_non_indent[:-1]
        else:
            body = stmt_non_indent

        # Check if question mark is at the end of the expression
        if body and body[-1].type == TokenType.QUESTION:
            body = body[:-1]  # remove '?'
            if add_explanation:
                add_explanation(stmt_non_indent[0].line, "? operator → early error unwrapping & return guard")
            tmp_id = next_counter()
            tmp_var = f"_rad_try_tmp_{tmp_id}"
            base_col = stmt_non_indent[0].col
            ref_line = stmt_non_indent[0].line

            # Emit leading indents first
            result.extend(leading_indents)

            # Check if statement starts with 'return'
            if body and body[0].type == TokenType.IDENTIFIER and body[0].value == "return":
                expr_tokens = body[1:]
                # 1: _rad_try_tmp = expr
                result.append(Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col))
                result.append(Token(TokenType.OP, "=", ref_line, base_col))
                result.extend(expr_tokens)
                result.append(Token(TokenType.NEWLINE, "\n", ref_line, base_col))

                # 2: if hasattr(_rad_try_tmp, 'is_err') and _rad_try_tmp.is_err(): return _rad_try_tmp
                result.extend([
                    Token(TokenType.IDENTIFIER, "if", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "hasattr", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.STRING, '"is_err"', ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "and", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.OP, ".", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "is_err", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.DELIMITER, ":", ref_line, base_col),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "return", ref_line, base_col + 4),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col + 4),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                ])

                # 3: if hasattr(_rad_try_tmp, 'is_none') and _rad_try_tmp.is_none(): return _rad_try_tmp
                result.extend([
                    Token(TokenType.IDENTIFIER, "if", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "hasattr", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.STRING, '"is_none"', ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "and", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.OP, ".", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "is_none", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.DELIMITER, ":", ref_line, base_col),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "return", ref_line, base_col + 4),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col + 4),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                ])

                # 4: return getattr(_rad_try_tmp, 'value', _rad_try_tmp)
                result.extend([
                    Token(TokenType.IDENTIFIER, "return", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "getattr", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.STRING, '"value"', ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                ])
                if newline_tok:
                    result.append(newline_tok)
                continue

            # Check if statement has '=' assignment at depth 0
            eq_idx = -1
            cur_depth = 0
            for idx, t in enumerate(body):
                if t.value in ("(", "[", "{"):
                    cur_depth += 1
                elif t.value in (")", "]", "}"):
                    cur_depth -= 1
                elif cur_depth == 0 and t.value == "=" and t.type == TokenType.OP:
                    eq_idx = idx
                    break

            if eq_idx != -1:
                target_tokens = body[:eq_idx]
                expr_tokens = body[eq_idx + 1:]

                # 1: _rad_try_tmp = expr
                result.append(Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col))
                result.append(Token(TokenType.OP, "=", ref_line, base_col))
                result.extend(expr_tokens)
                result.append(Token(TokenType.NEWLINE, "\n", ref_line, base_col))

                # 2: if hasattr(_rad_try_tmp, 'is_err') and _rad_try_tmp.is_err(): return _rad_try_tmp
                result.extend([
                    Token(TokenType.IDENTIFIER, "if", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "hasattr", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.STRING, '"is_err"', ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "and", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.OP, ".", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "is_err", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.DELIMITER, ":", ref_line, base_col),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "return", ref_line, base_col + 4),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col + 4),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                ])

                # 3: if hasattr(_rad_try_tmp, 'is_none') and _rad_try_tmp.is_none(): return _rad_try_tmp
                result.extend([
                    Token(TokenType.IDENTIFIER, "if", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "hasattr", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.STRING, '"is_none"', ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "and", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.OP, ".", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "is_none", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.DELIMITER, ":", ref_line, base_col),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "return", ref_line, base_col + 4),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col + 4),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                ])

                # 4: target = getattr(_rad_try_tmp, 'value', _rad_try_tmp)
                if target_tokens:
                    first_t = target_tokens[0]
                    target_tokens[0] = Token(first_t.type, first_t.value, first_t.line, base_col, first_t.end_line, first_t.end_col)
                result.extend(target_tokens)
                result.append(Token(TokenType.OP, "=", ref_line, base_col))
                result.extend([
                    Token(TokenType.IDENTIFIER, "getattr", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.STRING, '"value"', ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                ])
                if newline_tok:
                    result.append(newline_tok)
                continue
            else:
                # Standalone expression with ?
                # 1: _rad_try_tmp = expr
                result.append(Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col))
                result.append(Token(TokenType.OP, "=", ref_line, base_col))
                result.extend(body)
                result.append(Token(TokenType.NEWLINE, "\n", ref_line, base_col))

                # 2: if hasattr(_rad_try_tmp, 'is_err') and _rad_try_tmp.is_err(): return _rad_try_tmp
                result.extend([
                    Token(TokenType.IDENTIFIER, "if", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "hasattr", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.DELIMITER, ",", ref_line, base_col),
                    Token(TokenType.STRING, '"is_err"', ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "and", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col),
                    Token(TokenType.OP, ".", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "is_err", ref_line, base_col),
                    Token(TokenType.DELIMITER, "(", ref_line, base_col),
                    Token(TokenType.DELIMITER, ")", ref_line, base_col),
                    Token(TokenType.DELIMITER, ":", ref_line, base_col),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                    Token(TokenType.IDENTIFIER, "return", ref_line, base_col + 4),
                    Token(TokenType.IDENTIFIER, tmp_var, ref_line, base_col + 4),
                    Token(TokenType.NEWLINE, "\n", ref_line, base_col),
                ])
                if newline_tok:
                    result.append(newline_tok)
                continue

        result.extend(stmt)

    return result, True


def transform_ranges(
    tokens: list[Token],
    filename: str = "<string>",
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> list[Token]:
    """
    Transforms range tokens `start..end` and `start..=end` into `range(...)`.
    Supports optional step: `start..end..step`.
    """
    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type in (TokenType.RANGE_EXCLUSIVE, TokenType.RANGE_INCLUSIVE):
            inclusive = (tok.type == TokenType.RANGE_INCLUSIVE)
            # Find the left operand tokens by scanning backwards in result
            left_tokens = extract_left_operand(result)
            if not left_tokens:
                raise RadicalSyntaxError(
                    message="Missing start operand for range expression",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )

            # Scan forward for the right operand
            i += 1
            right_tokens, next_i = extract_right_operand(tokens, i)
            if not right_tokens:
                raise RadicalSyntaxError(
                    message="Missing end operand for range expression",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )

            # Check if there is a second `..` for step: `start..end..step`
            step_tokens: Optional[list[Token]] = None
            if next_i < n and tokens[next_i].type == TokenType.RANGE_EXCLUSIVE:
                step_tok = tokens[next_i]
                step_tokens, next_i = extract_right_operand(tokens, next_i + 1)

            # Construct `range(start, end)` or `range(start, (end) + 1)`
            range_tokens = build_range_tokens(
                left_tokens=left_tokens,
                right_tokens=right_tokens,
                step_tokens=step_tokens,
                inclusive=inclusive,
                ref_tok=tok,
            )
            result.extend(range_tokens)
            i = next_i
            continue

        result.append(tok)
        i += 1

    return result


def transform_coalescing(
    tokens: list[Token],
    filename: str = "<string>",
    counter_fn: Optional[Callable[[], int]] = None,
) -> list[Token]:
    """
    Transforms nullish coalescing tokens:
    - `a ?? b` into `(a if a is not None else b)` or ternary with :=
    - `a ??= b` into `a = (a if a is not None else b)`
    """
    local_counter = 0

    def next_counter() -> int:
        nonlocal local_counter
        if counter_fn is not None:
            return counter_fn()
        local_counter += 1
        return local_counter

    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.COALESCE_ASSIGN:
            target_tokens = extract_left_operand(result)
            if not target_tokens:
                raise RadicalSyntaxError(
                    message="Missing target for ??= assignment",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            i += 1
            value_tokens, next_i = extract_right_operand(tokens, i)
            if not value_tokens:
                raise RadicalSyntaxError(
                    message="Missing value for ??= assignment",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )

            # target = (target if target is not None else value)
            assign_tokens: list[Token] = []
            assign_tokens.extend(target_tokens)
            assign_tokens.append(Token(TokenType.OP, "=", tok.line, tok.col))
            assign_tokens.append(Token(TokenType.DELIMITER, "(", tok.line, tok.col))
            assign_tokens.extend(target_tokens)
            assign_tokens.append(Token(TokenType.IDENTIFIER, "if", tok.line, tok.col))
            assign_tokens.extend(target_tokens)
            assign_tokens.append(Token(TokenType.IDENTIFIER, "is", tok.line, tok.col))
            assign_tokens.append(Token(TokenType.IDENTIFIER, "not", tok.line, tok.col))
            assign_tokens.append(Token(TokenType.IDENTIFIER, "None", tok.line, tok.col))
            assign_tokens.append(Token(TokenType.IDENTIFIER, "else", tok.line, tok.col))
            assign_tokens.extend(value_tokens)
            assign_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))

            result.extend(assign_tokens)
            i = next_i
            continue

        if tok.type == TokenType.COALESCE:
            left_tokens = extract_left_operand(result)
            if not left_tokens:
                raise RadicalSyntaxError(
                    message="Missing left operand for ?? operator",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            i += 1
            right_tokens, next_i = extract_right_operand(tokens, i)
            if not right_tokens:
                raise RadicalSyntaxError(
                    message="Missing right operand for ?? operator",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )

            # If left is a simple identifier: (left if left is not None else right)
            # If left is complex: (_rad_c_1 if (_rad_c_1 := left) is not None else right)
            coalesce_tokens: list[Token] = [Token(TokenType.DELIMITER, "(", tok.line, tok.col)]
            if len(left_tokens) == 1 and left_tokens[0].type == TokenType.IDENTIFIER:
                coalesce_tokens.extend(left_tokens)
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "if", tok.line, tok.col))
                coalesce_tokens.extend(left_tokens)
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "is", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "not", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "None", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "else", tok.line, tok.col))
                coalesce_tokens.extend(right_tokens)
                coalesce_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))
            else:
                c_id = next_counter()
                var_name = f"_rad_c_{c_id}"
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, var_name, tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "if", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.DELIMITER, "(", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, var_name, tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.OP, ":=", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.DELIMITER, "(", tok.line, tok.col))
                coalesce_tokens.extend(left_tokens)
                coalesce_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "is", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "not", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "None", tok.line, tok.col))
                coalesce_tokens.append(Token(TokenType.IDENTIFIER, "else", tok.line, tok.col))
                coalesce_tokens.extend(right_tokens)
                coalesce_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))

            result.extend(coalesce_tokens)
            i = next_i
            continue

        result.append(tok)
        i += 1

    return result


def transform_safe_nav(
    tokens: list[Token],
    filename: str = "<string>",
) -> list[Token]:
    """
    Transforms safe navigation tokens:
    - `obj?.prop` into `_rad_safe_attr(obj, "prop")`
    - `obj?[key]` into `_rad_safe_item(obj, key)`
    - `func?.(*args)` into `_rad_safe_call(func, *args)`
    """
    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.SAFE_DOT:
            left_tokens = extract_left_operand(result)
            if not left_tokens:
                raise RadicalSyntaxError(
                    message="Missing target for safe navigation '?.'",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            if i + 1 >= n or tokens[i + 1].type not in (
                TokenType.IDENTIFIER, TokenType.KW_CONST, TokenType.KW_DEFER,
                TokenType.KW_STRUCT, TokenType.KW_RAW, TokenType.KW_PARALLEL
            ):
                raise RadicalSyntaxError(
                    message="Expected attribute name after '?.'",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            attr_tok = tokens[i + 1]
            nav_tokens: list[Token] = [
                Token(TokenType.IDENTIFIER, "_rad_safe_attr", tok.line, tok.col),
                Token(TokenType.DELIMITER, "(", tok.line, tok.col),
            ]
            nav_tokens.extend(left_tokens)
            nav_tokens.append(Token(TokenType.DELIMITER, ",", tok.line, tok.col))
            nav_tokens.append(Token(TokenType.STRING, f'"{attr_tok.value}"', attr_tok.line, attr_tok.col))
            nav_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))

            result.extend(nav_tokens)
            i += 2
            continue

        if tok.type == TokenType.SAFE_BRACKET:
            left_tokens = extract_left_operand(result)
            if not left_tokens:
                raise RadicalSyntaxError(
                    message="Missing target for safe indexing '?[",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            i += 1
            key_tokens: list[Token] = []
            depth = 1
            while i < n and depth > 0:
                curr = tokens[i]
                if curr.value == "[":
                    depth += 1
                elif curr.value == "]":
                    depth -= 1
                    if depth == 0:
                        i += 1
                        break
                key_tokens.append(curr)
                i += 1

            nav_tokens = [
                Token(TokenType.IDENTIFIER, "_rad_safe_item", tok.line, tok.col),
                Token(TokenType.DELIMITER, "(", tok.line, tok.col),
            ]
            nav_tokens.extend(left_tokens)
            nav_tokens.append(Token(TokenType.DELIMITER, ",", tok.line, tok.col))
            nav_tokens.extend(key_tokens)
            nav_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))

            result.extend(nav_tokens)
            continue

        if tok.type == TokenType.SAFE_CALL:
            left_tokens = extract_left_operand(result)
            if not left_tokens:
                raise RadicalSyntaxError(
                    message="Missing target for safe call '?.('",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            i += 1
            arg_tokens: list[Token] = []
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
                arg_tokens.append(curr)
                i += 1

            nav_tokens = [
                Token(TokenType.IDENTIFIER, "_rad_safe_call", tok.line, tok.col),
                Token(TokenType.DELIMITER, "(", tok.line, tok.col),
            ]
            nav_tokens.extend(left_tokens)
            if arg_tokens:
                nav_tokens.append(Token(TokenType.DELIMITER, ",", tok.line, tok.col))
                nav_tokens.extend(arg_tokens)
            nav_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))

            result.extend(nav_tokens)
            continue

        result.append(tok)
        i += 1

    return result
