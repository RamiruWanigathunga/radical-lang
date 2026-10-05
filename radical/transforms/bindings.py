"""
Radical Language Transforms: Variable Bindings.
Transforms `let` mutable bindings, `const` immutable declarations,
and object/dictionary destructuring syntax.
"""

from radical.token import Token, TokenType


def transform_let(tokens: list[Token]) -> list[Token]:
    """
    Transforms `let x = 1` or `let mut x = 1` or `let (a, b) = pair` or `let x: int = 1`
    into standard Python variable bindings.
    """
    result: list[Token] = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.KW_LET:
            let_col = tok.col
            i += 1
            # Skip optional 'mut' keyword
            if i < n and tokens[i].type == TokenType.IDENTIFIER and tokens[i].value == "mut":
                i += 1
            if i < n:
                next_tok = tokens[i]
                adjusted = Token(next_tok.type, next_tok.value, next_tok.line, let_col, next_tok.end_line, next_tok.end_col)
                result.append(adjusted)
                i += 1
            continue
        result.append(tok)
        i += 1
    return result


def transform_const(tokens: list[Token]) -> tuple[list[Token], list[tuple[str, int, int]]]:
    """
    Transforms `const x = expr` into `x = expr` while registering constants
    for compile-time invariant checking.
    """
    result: list[Token] = []
    constants: list[tuple[str, int, int]] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.KW_CONST:
            const_tok = tok
            i += 1
            first = True
            while i < n and not (tokens[i].type == TokenType.OP and tokens[i].value == "="):
                t = tokens[i]
                if t.type == TokenType.IDENTIFIER:
                    constants.append((t.value, t.line, t.col))
                if first:
                    t = Token(t.type, t.value, t.line, const_tok.col, t.end_line, t.end_col)
                    first = False
                result.append(t)
                i += 1
            continue

        result.append(tok)
        i += 1

    return result, constants


def parse_destruct_field(field_tokens: list[Token]) -> tuple[str, str, int, int]:
    """Parses `field` or `field: alias` inside destructuring."""
    has_colon = any(t.value == ":" for t in field_tokens)
    if has_colon:
        colon_idx = next(i for i, t in enumerate(field_tokens) if t.value == ":")
        src = field_tokens[colon_idx - 1].value
        tgt = field_tokens[colon_idx + 1].value
        line = field_tokens[0].line
        col = field_tokens[0].col
        return src, tgt, line, col
    src = field_tokens[0].value
    return src, src, field_tokens[0].line, field_tokens[0].col


def transform_destructuring(tokens: list[Token]) -> tuple[list[Token], list[tuple[str, int, int]]]:
    """
    Transforms dict/object destructuring:
    - `{ id, token } = res` or `const { id, token } = res`
    into attribute/key lookup statements.
    Returns transformed tokens and a list of declared constants if `const` was used.
    """
    result: list[Token] = []
    destruct_consts: list[tuple[str, int, int]] = []
    i = 0
    n = len(tokens)
    destruct_id = 0

    while i < n:
        tok = tokens[i]
        is_const = False
        start_i = i
        ref_tok = tok

        if tok.type == TokenType.KW_CONST and i + 1 < n and tokens[i + 1].value == "{":
            is_const = True
            i += 1
            tok = tokens[i]

        if tok.value == "{":
            close_brace_idx = -1
            d = 0
            for j in range(i, n):
                if tokens[j].value == "{":
                    d += 1
                elif tokens[j].value == "}":
                    d -= 1
                    if d == 0:
                        close_brace_idx = j
                        break
                elif tokens[j].type in (TokenType.NEWLINE, TokenType.EOF):
                    break

            if close_brace_idx != -1 and close_brace_idx + 1 < n and tokens[close_brace_idx + 1].value == "=":
                destruct_id += 1
                tmp_var = f"_rad_destruct_{destruct_id}"

                inner = tokens[i + 1:close_brace_idx]
                fields: list[tuple[str, str, int, int]] = []
                curr_tokens: list[Token] = []
                for t in inner:
                    if t.value == ",":
                        if curr_tokens:
                            src, tgt, l, c = parse_destruct_field(curr_tokens)
                            fields.append((src, tgt, l, c))
                            curr_tokens = []
                        continue
                    curr_tokens.append(t)
                if curr_tokens:
                    src, tgt, l, c = parse_destruct_field(curr_tokens)
                    fields.append((src, tgt, l, c))

                eq_idx = close_brace_idx + 1
                source_expr_tokens: list[Token] = []
                k = eq_idx + 1
                while k < n and tokens[k].type not in (TokenType.NEWLINE, TokenType.EOF):
                    source_expr_tokens.append(tokens[k])
                    k += 1

                line = ref_tok.line
                col = ref_tok.col

                destruct_tokens: list[Token] = [
                    Token(TokenType.IDENTIFIER, tmp_var, line, col),
                    Token(TokenType.OP, "=", line, col),
                ]
                destruct_tokens.extend(source_expr_tokens)
                destruct_tokens.append(Token(TokenType.NEWLINE, "\n", line, col))

                is_dict_var = f"_rad_is_dict_{destruct_id}"
                destruct_tokens.extend([
                    Token(TokenType.IDENTIFIER, is_dict_var, line, col),
                    Token(TokenType.OP, "=", line, col),
                    Token(TokenType.IDENTIFIER, "type", line, col),
                    Token(TokenType.DELIMITER, "(", line, col),
                    Token(TokenType.IDENTIFIER, tmp_var, line, col),
                    Token(TokenType.DELIMITER, ")", line, col),
                    Token(TokenType.IDENTIFIER, "is", line, col),
                    Token(TokenType.IDENTIFIER, "dict", line, col),
                    Token(TokenType.NEWLINE, "\n", line, col),
                ])

                for src_name, tgt_name, f_line, f_col in fields:
                    if is_const:
                        destruct_consts.append((tgt_name, f_line, f_col))

                    destruct_tokens.extend([
                        Token(TokenType.IDENTIFIER, tgt_name, f_line, col),
                        Token(TokenType.OP, "=", f_line, col),
                        Token(TokenType.IDENTIFIER, tmp_var, f_line, col),
                        Token(TokenType.DELIMITER, "[", f_line, col),
                        Token(TokenType.STRING, f'"{src_name}"', f_line, col),
                        Token(TokenType.DELIMITER, "]", f_line, col),
                        Token(TokenType.IDENTIFIER, "if", f_line, col),
                        Token(TokenType.IDENTIFIER, is_dict_var, f_line, col),
                        Token(TokenType.IDENTIFIER, "else", f_line, col),
                        Token(TokenType.IDENTIFIER, "getattr", f_line, col),
                        Token(TokenType.DELIMITER, "(", f_line, col),
                        Token(TokenType.IDENTIFIER, tmp_var, f_line, col),
                        Token(TokenType.DELIMITER, ",", f_line, col),
                        Token(TokenType.STRING, f'"{src_name}"', f_line, col),
                        Token(TokenType.DELIMITER, ")", f_line, col),
                        Token(TokenType.NEWLINE, "\n", f_line, col),
                    ])

                result.extend(destruct_tokens)
                i = k
                continue

        result.append(tokens[start_i])
        i = start_i + 1

    return result, destruct_consts
