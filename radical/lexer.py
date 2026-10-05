"""
Radical Language Lexer and Token Preprocessor.
Tokenizes Radical source code using a token-stream post-processor over Python's tokenizer.
Preserves comments, strings, indentation, and accurately maps line and column positions.
"""

import io
import tokenize as py_tokenize
from typing import Iterator, Optional
from radical.token import Token, TokenType
from radical.exceptions import RadicalSyntaxError


KEYWORDS_MAP = {
    "const": TokenType.KW_CONST,
    "defer": TokenType.KW_DEFER,
    "struct": TokenType.KW_STRUCT,
    "raw": TokenType.KW_RAW,
    "parallel": TokenType.KW_PARALLEL,
    "fn": TokenType.KW_FN,
    "gpu": TokenType.KW_GPU,
    "let": TokenType.KW_LET,
    "using": TokenType.KW_USING,
    "enum": TokenType.KW_ENUM,
    "unsafe": TokenType.KW_UNSAFE,
    "native": TokenType.KW_NATIVE,
    "trait": TokenType.KW_TRAIT,
    "select": TokenType.KW_SELECT,
}


class RadicalLexer:
    """
    Scans Radical source text and yields a sequence of Token objects.
    """
    def __init__(self, filename: str = "<string>") -> None:
        self.filename = filename

    def tokenize(self, source: str) -> list[Token]:
        """Tokenize the full source string into a list of Radical Tokens."""
        # Convert source to bytes for py_tokenize.tokenize
        source_bytes = source.encode("utf-8")
        readline = io.BytesIO(source_bytes).readline

        raw_tokens: list[py_tokenize.TokenInfo] = []
        try:
            for tok in py_tokenize.tokenize(readline):
                # Ignore ENCODING header token
                if tok.type == py_tokenize.ENCODING:
                    continue
                raw_tokens.append(tok)
        except py_tokenize.TokenError as e:
            msg, (line, col) = e.args
            raise RadicalSyntaxError(
                message=f"Syntax error during tokenization: {msg}",
                filename=self.filename,
                lineno=line,
                col_offset=col,
            ) from e

        # Post-process raw token stream to combine multi-character Radical operators
        radical_tokens = self._fuse_radical_tokens(raw_tokens)
        return radical_tokens

    def _fuse_radical_tokens(self, raw: list[py_tokenize.TokenInfo]) -> list[Token]:
        result: list[Token] = []
        i = 0
        n = len(raw)

        while i < n:
            tok = raw[i]
            t_type = tok.type
            t_str = tok.string
            s_line, s_col = tok.start
            e_line, e_col = tok.end

            # Check for EOF
            if t_type == py_tokenize.ENDMARKER:
                result.append(Token(TokenType.EOF, "", s_line, s_col, e_line, e_col))
                i += 1
                continue

            # Check for Comments
            if t_type == py_tokenize.COMMENT:
                result.append(Token(TokenType.COMMENT, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue

            # Check for Strings
            if t_type == py_tokenize.STRING:
                result.append(Token(TokenType.STRING, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue

            # Check for Indentation
            if t_type == py_tokenize.INDENT:
                result.append(Token(TokenType.INDENT, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue
            if t_type == py_tokenize.DEDENT:
                result.append(Token(TokenType.DEDENT, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue
            if t_type in (py_tokenize.NEWLINE, py_tokenize.NL):
                result.append(Token(TokenType.NEWLINE, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue

            # Check for range starting with float like '0.' followed by '.' or '.=' or '.10'
            if t_type == py_tokenize.NUMBER and t_str.endswith(".") and not t_str.endswith("..") and i + 1 < n:
                next_tok = raw[i + 1]
                if next_tok.type == py_tokenize.NUMBER and next_tok.string.startswith("."):
                    # e.g., '0.' followed by '.10' -> '0', '..', '10'
                    num1 = t_str[:-1]
                    num2 = next_tok.string[1:]
                    result.append(Token(TokenType.NUMBER, num1, s_line, s_col, e_line, e_col - 1))
                    result.append(Token(TokenType.RANGE_EXCLUSIVE, "..", s_line, e_col - 1, next_tok.start[0], next_tok.start[1] + 1))
                    result.append(Token(TokenType.NUMBER, num2, next_tok.start[0], next_tok.start[1] + 1, next_tok.end[0], next_tok.end[1]))
                    i += 2
                    continue
                elif next_tok.string == "=" and i + 2 < n and raw[i + 2].string == "=":
                    pass  # Not a range
                elif next_tok.string == ".":
                    # We have `<number>.` followed by `.`
                    # Check if next after that is `=` -> `..=`
                    num_val = t_str[:-1]
                    result.append(Token(TokenType.NUMBER, num_val, s_line, s_col, e_line, e_col - 1))
                    if i + 2 < n and raw[i + 2].string == "=":
                        result.append(Token(TokenType.RANGE_INCLUSIVE, "..=", s_line, e_col - 1, raw[i + 2].end[0], raw[i + 2].end[1]))
                        i += 3
                        continue
                    else:
                        result.append(Token(TokenType.RANGE_EXCLUSIVE, "..", s_line, e_col - 1, next_tok.end[0], next_tok.end[1]))
                        i += 2
                        continue

            # Check for Pipeline operator `|>`
            if t_str == "|" and i + 1 < n and raw[i + 1].string == ">":
                result.append(Token(TokenType.PIPE, "|>", s_line, s_col, raw[i + 1].end[0], raw[i + 1].end[1]))
                i += 2
                continue

            # Check for Arrow function operator `=>`
            if t_str == "=" and i + 1 < n and raw[i + 1].string == ">":
                result.append(Token(TokenType.ARROW, "=>", s_line, s_col, raw[i + 1].end[0], raw[i + 1].end[1]))
                i += 2
                continue

            # Check for Safe Navigation `?.(`, `?.`, `?[`
            if t_str == "?" and i + 1 < n and raw[i + 1].string == ".":
                if i + 2 < n and raw[i + 2].string == "(":
                    result.append(Token(TokenType.SAFE_CALL, "?.(", s_line, s_col, raw[i + 2].end[0], raw[i + 2].end[1]))
                    i += 3
                    continue
                result.append(Token(TokenType.SAFE_DOT, "?.", s_line, s_col, raw[i + 1].end[0], raw[i + 1].end[1]))
                i += 2
                continue

            if t_str == "?" and i + 1 < n and raw[i + 1].string == "[":
                result.append(Token(TokenType.SAFE_BRACKET, "?[", s_line, s_col, raw[i + 1].end[0], raw[i + 1].end[1]))
                i += 2
                continue

            # Check for Nullish Coalescing `??=` and `??`
            if t_str == "?" and i + 1 < n and raw[i + 1].string == "?":
                if i + 2 < n and raw[i + 2].string == "=":
                    result.append(Token(TokenType.COALESCE_ASSIGN, "??=", s_line, s_col, raw[i + 2].end[0], raw[i + 2].end[1]))
                    i += 3
                    continue
                result.append(Token(TokenType.COALESCE, "??", s_line, s_col, raw[i + 1].end[0], raw[i + 1].end[1]))
                i += 2
                continue

            # Check for standalone '?' (try / error unwrap operator)
            if t_str == "?":
                result.append(Token(TokenType.QUESTION, "?", s_line, s_col, e_line, e_col))
                i += 1
                continue

            # Check for Range operators `..=` and `..` on dots
            if t_str == "." and i + 1 < n and raw[i + 1].type == py_tokenize.NUMBER and raw[i + 1].string.startswith("."):
                num2 = raw[i + 1].string[1:]
                result.append(Token(TokenType.RANGE_EXCLUSIVE, "..", s_line, s_col, raw[i + 1].start[0], raw[i + 1].start[1] + 1))
                result.append(Token(TokenType.NUMBER, num2, raw[i + 1].start[0], raw[i + 1].start[1] + 1, raw[i + 1].end[0], raw[i + 1].end[1]))
                i += 2
                continue

            if t_str == "." and i + 1 < n and raw[i + 1].string == ".":
                if i + 2 < n and raw[i + 2].string == "=":
                    result.append(Token(TokenType.RANGE_INCLUSIVE, "..=", s_line, s_col, raw[i + 2].end[0], raw[i + 2].end[1]))
                    i += 3
                    continue
                result.append(Token(TokenType.RANGE_EXCLUSIVE, "..", s_line, s_col, raw[i + 1].end[0], raw[i + 1].end[1]))
                i += 2
                continue

            # Check for Keywords
            if t_type == py_tokenize.NAME:
                if t_str in KEYWORDS_MAP:
                    result.append(Token(KEYWORDS_MAP[t_str], t_str, s_line, s_col, e_line, e_col))
                    i += 1
                    continue
                result.append(Token(TokenType.IDENTIFIER, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue

            if t_type == py_tokenize.NUMBER:
                result.append(Token(TokenType.NUMBER, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue

            # Other Operators / Delimiters
            if t_type == py_tokenize.OP:
                result.append(Token(TokenType.OP, t_str, s_line, s_col, e_line, e_col))
                i += 1
                continue

            # Fallback
            result.append(Token(TokenType.DELIMITER, t_str, s_line, s_col, e_line, e_col))
            i += 1

        return result
