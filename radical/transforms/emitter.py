"""
Source code emission from token streams for Radical transpiler.
"""

from typing import Optional
from radical.lexer import Token, TokenType


def tokens_to_source(tokens: list[Token]) -> str:
    """Reconstruct source text from token stream with accurate indentation."""
    parts = []
    last_tok: Optional[Token] = None
    at_line_start = True

    for tok in tokens:
        if tok.type == TokenType.EOF:
            continue

        if tok.type in (TokenType.INDENT, TokenType.DEDENT):
            continue

        if tok.type == TokenType.NEWLINE:
            parts.append("\n")
            last_tok = tok
            at_line_start = True
            continue

        if at_line_start:
            if tok.col > 0:
                parts.append(" " * tok.col)
            at_line_start = False
        elif last_tok is not None:
            needs_space = False
            if tok.value in (")", "]", "}", ":", ","):
                needs_space = False
            elif last_tok.value in ("(", "[", "{", "@"):
                needs_space = False
            elif last_tok.type.name.startswith(("IDENTIFIER", "NUMBER", "STRING", "KW_")) and \
               tok.type.name.startswith(("IDENTIFIER", "NUMBER", "STRING", "KW_")):
                needs_space = True
            elif last_tok.type.name.startswith(("IDENTIFIER", "NUMBER", "STRING", "KW_")) and \
               any(tok.value.startswith(prefix) for prefix in ('"', "'", 'f"', "f'", 'r"', "r'", 'b"', "b'", 'fr"', 'rf"')):
                needs_space = True
            elif tok.value in ("in", "and", "or", "is", "not", "if", "for", "lambda", "+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">="):
                needs_space = True
            elif last_tok.value in ("in", "and", "or", "is", "not", "if", "for", "lambda", "return", "yield", "assert", "raise", "+", "-", "*", "/", "%", "=", "==", "!=", "<", ">", "<=", ">=", ","):
                needs_space = True

            if needs_space:
                parts.append(" ")

        parts.append(tok.value)
        last_tok = tok

    return "".join(parts)
