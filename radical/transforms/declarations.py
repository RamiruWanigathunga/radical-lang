"""
Radical Language Transforms: Declarations.
Transforms `native fn`, `fn` (Mojo-style typed functions), `struct`, `enum`,
`trait` (structural typing protocols), and `raw` continuous ctypes memory buffers.
"""

from typing import Callable, Optional
from radical.token import Token, TokenType
from radical.exceptions import RadicalSyntaxError, RadicalCompileError


def transform_native_fn(
    tokens: list[Token],
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms `native fn <name>(...):` into:
    `@_rad_native\nfn <name>(...):`
    """
    has_native = any(t.type == TokenType.KW_NATIVE for t in tokens)
    if not has_native:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)
    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.KW_NATIVE and i + 1 < n and tokens[i + 1].type == TokenType.KW_FN:
            ref_line = tok.line
            ref_col = tok.col
            if add_explanation is not None:
                add_explanation(ref_line, "native fn → compiled tier (Numba JIT / fast numerical fallback)")
            i += 1
            result.append(Token(TokenType.OP, "@", ref_line, ref_col))
            result.append(Token(TokenType.IDENTIFIER, "_rad_native", ref_line, ref_col))
            result.append(Token(TokenType.NEWLINE, "\n", ref_line, ref_col))
            fn_tok = tokens[i]
            result.append(Token(fn_tok.type, fn_tok.value, fn_tok.line, ref_col, fn_tok.end_line, fn_tok.end_col))
            i += 1
            continue

        result.append(tok)
        i += 1
    return result, True


def transform_enums(
    tokens: list[Token],
    filename: str = "<string>",
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms `enum Name: Variant1, Variant2` or ADT variants `Variant(fields...)`
    into pattern-matchable Python classes.
    """
    has_enum = any(t.type == TokenType.KW_ENUM for t in tokens)
    if not has_enum:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.KW_ENUM:
            if add_explanation is not None:
                add_explanation(tok.line, "enum ADT → pattern-matchable algebraic data type")
            i += 1
            if i >= n or tokens[i].type != TokenType.IDENTIFIER:
                raise RadicalSyntaxError("Expected enum name after 'enum'", filename=filename, lineno=tok.line, col_offset=tok.col)
            enum_name = tokens[i].value
            enum_line = tok.line
            enum_col = tok.col
            i += 1

            # Skip optional type parameters: enum Result[T, E]:
            if i < n and tokens[i].value == "[":
                depth = 1
                i += 1
                while i < n and depth > 0:
                    if tokens[i].value == "[": depth += 1
                    elif tokens[i].value == "]": depth -= 1
                    i += 1

            if i >= n or tokens[i].value != ":":
                raise RadicalSyntaxError(f"Expected ':' after enum name '{enum_name}'", filename=filename, lineno=tok.line, col_offset=tok.col)
            i += 1

            variants: list[tuple[str, list[str]]] = []
            enum_indent = enum_col

            if i < n and tokens[i].type in (TokenType.NEWLINE, TokenType.INDENT):
                while i < n and tokens[i].type in (TokenType.NEWLINE, TokenType.INDENT):
                    i += 1

            while i < n:
                curr = tokens[i]
                if curr.type == TokenType.DEDENT:
                    i += 1
                    break
                if curr.type in (TokenType.NEWLINE, TokenType.COMMENT):
                    i += 1
                    continue
                if curr.col <= enum_indent and curr.type not in (TokenType.NEWLINE, TokenType.COMMENT):
                    break

                if curr.type == TokenType.IDENTIFIER:
                    var_name = curr.value
                    var_fields: list[str] = []
                    i += 1
                    if i < n and tokens[i].value == "(":
                        i += 1
                        field_depth = 1
                        field_name = ""
                        while i < n and field_depth > 0:
                            ftok = tokens[i]
                            if ftok.value == "(":
                                field_depth += 1
                            elif ftok.value == ")":
                                field_depth -= 1
                                if field_depth == 0:
                                    if field_name.strip():
                                        var_fields.append(field_name.strip())
                                    i += 1
                                    break
                            elif ftok.value == "," and field_depth == 1:
                                if field_name.strip():
                                    var_fields.append(field_name.strip())
                                    field_name = ""
                                i += 1
                                continue
                            else:
                                field_name += (" " + ftok.value if field_name else ftok.value)
                            i += 1
                    variants.append((var_name, var_fields))
                    continue
                i += 1

            has_fields = any(len(fields) > 0 for _, fields in variants)

            cls_tokens: list[Token] = [
                Token(TokenType.IDENTIFIER, "class", enum_line, enum_col),
                Token(TokenType.IDENTIFIER, enum_name, enum_line, enum_col),
                Token(TokenType.DELIMITER, ":", enum_line, enum_col),
                Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
            ]

            if not has_fields:
                for vname, _ in variants:
                    cls_tokens.extend([
                        Token(TokenType.IDENTIFIER, "    " + vname, enum_line, enum_col + 4),
                        Token(TokenType.OP, "=", enum_line, enum_col + 4),
                        Token(TokenType.STRING, f'"{vname}"', enum_line, enum_col + 4),
                        Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                    ])
                if not variants:
                    cls_tokens.extend([
                        Token(TokenType.IDENTIFIER, "    pass", enum_line, enum_col + 4),
                        Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                    ])
            else:
                cls_tokens.extend([
                    Token(TokenType.IDENTIFIER, "    pass", enum_line, enum_col + 4),
                    Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                ])
                for vname, fields in variants:
                    cls_tokens.extend([
                        Token(TokenType.OP, "@", enum_line, enum_col),
                        Token(TokenType.IDENTIFIER, "dataclass", enum_line, enum_col),
                        Token(TokenType.DELIMITER, "(", enum_line, enum_col),
                        Token(TokenType.IDENTIFIER, "frozen", enum_line, enum_col),
                        Token(TokenType.OP, "=", enum_line, enum_col),
                        Token(TokenType.IDENTIFIER, "True", enum_line, enum_col),
                        Token(TokenType.DELIMITER, ")", enum_line, enum_col),
                        Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                        Token(TokenType.IDENTIFIER, "class", enum_line, enum_col),
                        Token(TokenType.IDENTIFIER, vname, enum_line, enum_col),
                        Token(TokenType.DELIMITER, "(", enum_line, enum_col),
                        Token(TokenType.IDENTIFIER, enum_name, enum_line, enum_col),
                        Token(TokenType.DELIMITER, ")", enum_line, enum_col),
                        Token(TokenType.DELIMITER, ":", enum_line, enum_col),
                        Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                    ])
                    if fields:
                        for f in fields:
                            f_decl = f if ":" in f else f"{f}: typing.Any = None"
                            cls_tokens.extend([
                                Token(TokenType.IDENTIFIER, "    " + f_decl, enum_line, enum_col + 4),
                                Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                            ])
                    else:
                        cls_tokens.extend([
                            Token(TokenType.IDENTIFIER, "    pass", enum_line, enum_col + 4),
                            Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                        ])
                    cls_tokens.extend([
                        Token(TokenType.IDENTIFIER, f"{enum_name}.{vname}", enum_line, enum_col),
                        Token(TokenType.OP, "=", enum_line, enum_col),
                        Token(TokenType.IDENTIFIER, vname, enum_line, enum_col),
                        Token(TokenType.NEWLINE, "\n", enum_line, enum_col),
                    ])

            result.extend(cls_tokens)
            continue

        result.append(tok)
        i += 1

    return result, True


def transform_traits(
    tokens: list[Token],
    filename: str = "<string>",
    add_explanation: Optional[Callable[[int, str], None]] = None,
) -> tuple[list[Token], bool]:
    """
    Transforms `trait Name:` or `trait Name[T]:` into
    `@typing.runtime_checkable\nclass Name(typing.Protocol):`.
    """
    has_trait = any(t.type == TokenType.KW_TRAIT for t in tokens)
    if not has_trait:
        return tokens, False

    result: list[Token] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]
        if tok.type == TokenType.KW_TRAIT:
            if add_explanation is not None:
                add_explanation(tok.line, "trait → typing.Protocol declaration")
            trait_line = tok.line
            trait_col = tok.col
            i += 1
            if i >= n or tokens[i].type != TokenType.IDENTIFIER:
                raise RadicalSyntaxError("Expected trait name after 'trait'", filename=filename, lineno=tok.line, col_offset=tok.col)
            trait_name = tokens[i].value
            i += 1

            type_args: list[Token] = []
            if i < n and tokens[i].value == "[":
                depth = 1
                type_args.append(tokens[i])
                i += 1
                while i < n and depth > 0:
                    type_args.append(tokens[i])
                    if tokens[i].value == "[": depth += 1
                    elif tokens[i].value == "]": depth -= 1
                    i += 1

            if i >= n or tokens[i].value != ":":
                raise RadicalSyntaxError(f"Expected ':' after trait name '{trait_name}'", filename=filename, lineno=tok.line, col_offset=tok.col)
            i += 1

            cls_tokens: list[Token] = [
                Token(TokenType.OP, "@", trait_line, trait_col),
                Token(TokenType.IDENTIFIER, "typing", trait_line, trait_col),
                Token(TokenType.OP, ".", trait_line, trait_col),
                Token(TokenType.IDENTIFIER, "runtime_checkable", trait_line, trait_col),
                Token(TokenType.NEWLINE, "\n", trait_line, trait_col),
                Token(TokenType.IDENTIFIER, "class", trait_line, trait_col),
                Token(TokenType.IDENTIFIER, trait_name, trait_line, trait_col),
            ]
            if type_args:
                cls_tokens.extend(type_args)
            cls_tokens.extend([
                Token(TokenType.DELIMITER, "(", trait_line, trait_col),
                Token(TokenType.IDENTIFIER, "typing", trait_line, trait_col),
                Token(TokenType.OP, ".", trait_line, trait_col),
                Token(TokenType.IDENTIFIER, "Protocol", trait_line, trait_col),
                Token(TokenType.DELIMITER, ")", trait_line, trait_col),
                Token(TokenType.DELIMITER, ":", trait_line, trait_col),
                Token(TokenType.NEWLINE, "\n", trait_line, trait_col),
            ])
            result.extend(cls_tokens)
            continue

        result.append(tok)
        i += 1

    return result, True


def transform_fn_functions(
    tokens: list[Token],
    filename: str = "<string>",
) -> tuple[list[Token], list[tuple[str, int, int]]]:
    """
    Transforms Mojo-style `fn name(...) -> type:` strict functions into `def name(...) -> type:`
    while enforcing static type annotations on all parameters and registering borrowed immutable parameters.
    """
    result: list[Token] = []
    borrowed_consts: list[tuple[str, int, int]] = []
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.KW_FN:
            ref_line = tok.line
            ref_col = tok.col
            i += 1
            if i >= n or tokens[i].type != TokenType.IDENTIFIER:
                raise RadicalSyntaxError(
                    message="Expected function name after 'fn'",
                    filename=filename,
                    lineno=ref_line,
                    col_offset=ref_col,
                )
            fn_name_tok = tokens[i]
            i += 1

            if i >= n or tokens[i].value != "(":
                raise RadicalSyntaxError(
                    message="Expected '(' after function name in 'fn' declaration",
                    filename=filename,
                    lineno=ref_line,
                    col_offset=ref_col,
                )
            i += 1

            param_groups: list[list[Token]] = []
            curr_param: list[Token] = []
            depth = 1

            while i < n and depth > 0:
                curr = tokens[i]
                if curr.value == "(":
                    depth += 1
                elif curr.value == ")":
                    depth -= 1
                    if depth == 0:
                        if curr_param:
                            param_groups.append(curr_param)
                        i += 1
                        break
                elif curr.value == "," and depth == 1:
                    if curr_param:
                        param_groups.append(curr_param)
                        curr_param = []
                    i += 1
                    continue

                curr_param.append(curr)
                i += 1

            for param_tokens in param_groups:
                if not param_tokens:
                    continue
                p_name_tok = param_tokens[0]
                p_name = p_name_tok.value
                if p_name in ("self", "cls"):
                    continue
                has_type = any(t.value == ":" for t in param_tokens)
                if not has_type:
                    raise RadicalCompileError(
                        message=f"Mojo-style 'fn' requires static type annotations on all parameters; parameter '{p_name}' is missing a type",
                        filename=filename,
                        lineno=p_name_tok.line,
                        col_offset=p_name_tok.col,
                    )
                borrowed_consts.append((p_name, p_name_tok.line, p_name_tok.col))

            result.append(Token(TokenType.IDENTIFIER, "def", ref_line, ref_col))
            result.append(fn_name_tok)
            result.append(Token(TokenType.DELIMITER, "(", ref_line, ref_col))
            for idx, pg in enumerate(param_groups):
                result.extend(pg)
                if idx < len(param_groups) - 1:
                    result.append(Token(TokenType.DELIMITER, ",", ref_line, ref_col))
            result.append(Token(TokenType.DELIMITER, ")", ref_line, ref_col))
            continue

        result.append(tok)
        i += 1

    return result, borrowed_consts


def transform_structs(
    tokens: list[Token],
    filename: str = "<string>",
) -> tuple[list[Token], bool]:
    """
    Transforms `struct Point(x: float, y: float)` or multiline `struct Name:`
    into `@dataclass(slots=True, frozen=True) class Name: ...`.
    Returns transformed tokens and a boolean indicating whether dataclass import is required.
    """
    result: list[Token] = []
    requires_dataclass = False
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.KW_STRUCT:
            requires_dataclass = True
            i += 1
            if i >= n or tokens[i].type != TokenType.IDENTIFIER:
                raise RadicalSyntaxError(
                    message="Expected struct name after 'struct'",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            name_tok = tokens[i]
            i += 1

            # Single-line struct Point(...)
            if i < n and tokens[i].value == "(":
                i += 1
                fields_tokens: list[list[Token]] = []
                curr_field: list[Token] = []
                depth = 1

                while i < n and depth > 0:
                    curr = tokens[i]
                    if curr.value == "(":
                        depth += 1
                    elif curr.value == ")":
                        depth -= 1
                        if depth == 0:
                            if curr_field:
                                fields_tokens.append(curr_field)
                            i += 1
                            break
                    elif curr.value == "," and depth == 1:
                        if curr_field:
                            fields_tokens.append(curr_field)
                            curr_field = []
                        i += 1
                        continue

                    curr_field.append(curr)
                    i += 1

                struct_tokens: list[Token] = [
                    Token(TokenType.OP, "@", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "dataclass", tok.line, tok.col),
                    Token(TokenType.DELIMITER, "(", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "slots", tok.line, tok.col),
                    Token(TokenType.OP, "=", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "True", tok.line, tok.col),
                    Token(TokenType.DELIMITER, ",", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "frozen", tok.line, tok.col),
                    Token(TokenType.OP, "=", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "True", tok.line, tok.col),
                    Token(TokenType.DELIMITER, ")", tok.line, tok.col),
                    Token(TokenType.NEWLINE, "\n", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "class", tok.line, tok.col),
                    name_tok,
                    Token(TokenType.DELIMITER, ":", tok.line, tok.col),
                    Token(TokenType.NEWLINE, "\n", tok.line, tok.col),
                    Token(TokenType.INDENT, "    ", tok.line, tok.col),
                ]

                if not fields_tokens:
                    struct_tokens.append(Token(TokenType.IDENTIFIER, "pass", tok.line, tok.col + 4))
                    struct_tokens.append(Token(TokenType.NEWLINE, "\n", tok.line, tok.col))
                else:
                    field_col = tok.col + 4
                    for f_idx, field in enumerate(fields_tokens):
                        has_annotation = any(t.value == ":" for t in field)
                        indented_field = [
                            Token(t.type, t.value, t.line, field_col if idx == 0 else t.col, t.end_line, t.end_col)
                            for idx, t in enumerate(field)
                        ]
                        if not has_annotation:
                            ident = indented_field[0]
                            rest = indented_field[1:]
                            struct_tokens.append(ident)
                            struct_tokens.append(Token(TokenType.DELIMITER, ":", tok.line, tok.col))
                            struct_tokens.append(Token(TokenType.IDENTIFIER, "typing.Any", tok.line, tok.col))
                            struct_tokens.extend(rest)
                        else:
                            struct_tokens.extend(indented_field)
                        struct_tokens.append(Token(TokenType.NEWLINE, "\n", tok.line, tok.col))

                result.extend(struct_tokens)
                continue

            elif i < n and tokens[i].value == ":":
                # Multiline block struct Name:
                struct_tokens = [
                    Token(TokenType.OP, "@", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "dataclass", tok.line, tok.col),
                    Token(TokenType.DELIMITER, "(", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "slots", tok.line, tok.col),
                    Token(TokenType.OP, "=", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "True", tok.line, tok.col),
                    Token(TokenType.DELIMITER, ",", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "frozen", tok.line, tok.col),
                    Token(TokenType.OP, "=", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "True", tok.line, tok.col),
                    Token(TokenType.DELIMITER, ")", tok.line, tok.col),
                    Token(TokenType.NEWLINE, "\n", tok.line, tok.col),
                    Token(TokenType.IDENTIFIER, "class", tok.line, tok.col),
                    name_tok,
                    tokens[i],
                ]
                i += 1
                result.extend(struct_tokens)
                continue

        result.append(tok)
        i += 1

    return result, requires_dataclass


def transform_raw_buffers(
    tokens: list[Token],
    filename: str = "<string>",
) -> tuple[list[Token], bool]:
    """
    Transforms `raw buf[size]:` or `raw buf[size, dtype]:` into
    `buf = (ctypes.c_uint8 * size)()`.
    Returns transformed tokens and a boolean indicating whether ctypes import is required.
    """
    result: list[Token] = []
    requires_ctypes = False
    i = 0
    n = len(tokens)

    while i < n:
        tok = tokens[i]

        if tok.type == TokenType.KW_RAW:
            requires_ctypes = True
            i += 1
            if i >= n or tokens[i].type != TokenType.IDENTIFIER:
                raise RadicalSyntaxError(
                    message="Expected buffer name after 'raw'",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            buf_name_tok = tokens[i]
            i += 1

            if i >= n or tokens[i].value != "[":
                raise RadicalSyntaxError(
                    message="Expected '[' after buffer name in raw declaration",
                    filename=filename,
                    lineno=tok.line,
                    col_offset=tok.col,
                )
            i += 1

            bracket_tokens: list[Token] = []
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
                bracket_tokens.append(curr)
                i += 1

            size_tokens: list[Token] = []
            dtype_name = "c_uint8"
            has_comma = False
            for b in bracket_tokens:
                if b.value == ",":
                    has_comma = True
                    continue
                if has_comma:
                    dtype_name = b.value
                    if not dtype_name.startswith("c_"):
                        dtype_name = f"c_{dtype_name}"
                else:
                    size_tokens.append(b)

            has_colon = False
            if i < n and tokens[i].value == ":":
                has_colon = True
                i += 1

            raw_tokens: list[Token] = [
                Token(TokenType.IDENTIFIER, buf_name_tok.value, tok.line, tok.col),
                Token(TokenType.OP, "=", tok.line, tok.col),
                Token(TokenType.DELIMITER, "(", tok.line, tok.col),
                Token(TokenType.IDENTIFIER, "ctypes", tok.line, tok.col),
                Token(TokenType.OP, ".", tok.line, tok.col),
                Token(TokenType.IDENTIFIER, dtype_name, tok.line, tok.col),
                Token(TokenType.OP, "*", tok.line, tok.col),
            ]
            raw_tokens.extend(size_tokens)
            raw_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))
            raw_tokens.append(Token(TokenType.DELIMITER, "(", tok.line, tok.col))
            raw_tokens.append(Token(TokenType.DELIMITER, ")", tok.line, tok.col))

            result.extend(raw_tokens)

            if has_colon:
                raw_indent = tok.col
                while i < n:
                    curr = tokens[i]
                    if curr.type in (TokenType.INDENT, TokenType.DEDENT):
                        i += 1
                        continue
                    if curr.type not in (TokenType.NEWLINE, TokenType.COMMENT, TokenType.EOF):
                        if curr.col <= raw_indent:
                            break
                        new_col = max(0, curr.col - 4)
                        curr = Token(curr.type, curr.value, curr.line, new_col, curr.end_line, max(0, curr.end_col - 4))
                    result.append(curr)
                    i += 1

            continue

        result.append(tok)
        i += 1

    return result, requires_ctypes
