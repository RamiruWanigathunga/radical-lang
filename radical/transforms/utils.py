"""
Radical Language Token Stream Utilities.
Shared helper functions for token pattern matching, balanced delimiter search,
and token stream manipulation across transformation passes.
"""

from typing import Callable, Optional, Sequence
from radical.token import Token, TokenType


def find_matching_delimiter(
    tokens: Sequence[Token],
    open_idx: int,
    open_delim: str = "(",
    close_delim: str = ")",
) -> int:
    """
    Finds the index of the matching closing delimiter given the index of an opening delimiter.
    Handles nested pairs accurately. Returns -1 if not found.
    """
    if open_idx >= len(tokens) or tokens[open_idx].value != open_delim:
        return -1

    depth = 0
    for idx in range(open_idx, len(tokens)):
        tok = tokens[idx]
        if tok.value == open_delim:
            depth += 1
        elif tok.value == close_delim:
            depth -= 1
            if depth == 0:
                return idx
    return -1


def find_next_token(
    tokens: Sequence[Token],
    start_idx: int,
    predicate: Callable[[Token], bool],
    stop_types: Sequence[TokenType] = (TokenType.NEWLINE, TokenType.EOF),
) -> int:
    """
    Scans forward from start_idx and returns the index of the first token satisfying
    predicate. If a token matching stop_types is reached before a match, returns -1.
    """
    for idx in range(start_idx, len(tokens)):
        tok = tokens[idx]
        if predicate(tok):
            return idx
        if tok.type in stop_types:
            return -1
    return -1


def split_token_sequence(
    tokens: Sequence[Token],
    delimiter_value: str = ",",
    skip_nested: bool = True,
) -> list[list[Token]]:
    """
    Splits a token sequence by a delimiter (e.g. comma), optionally ignoring delimiters
    inside nested parentheses, brackets, or braces.
    """
    parts: list[list[Token]] = []
    current: list[Token] = []
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0

    for tok in tokens:
        if skip_nested:
            if tok.value == "(": paren_depth += 1
            elif tok.value == ")": paren_depth = max(0, paren_depth - 1)
            elif tok.value == "[": bracket_depth += 1
            elif tok.value == "]": bracket_depth = max(0, bracket_depth - 1)
            elif tok.value == "{": brace_depth += 1
            elif tok.value == "}": brace_depth = max(0, brace_depth - 1)

        is_split = (
            tok.value == delimiter_value
            and (not skip_nested or (paren_depth == 0 and bracket_depth == 0 and brace_depth == 0))
        )

        if is_split:
            parts.append(current)
            current = []
        else:
            current.append(tok)

    if current or parts:
        parts.append(current)
    return parts


def make_token(
    token_type: TokenType,
    value: str,
    reference: Optional[Token] = None,
    line: int = 1,
    col: int = 0,
) -> Token:
    """
    Creates a new Token, inheriting line and column numbers from a reference token if provided.
    """
    if reference is not None:
        return Token(
            token_type,
            value,
            reference.line,
            reference.col,
            reference.end_line,
            reference.end_col,
        )
    return Token(token_type, value, line, col, line, col + len(value))
