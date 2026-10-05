"""
Radical Language Token Definitions.
Defines all token types including custom Radical syntactic operators and keywords.
"""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Optional


class TokenType(Enum):
    # Standard Python Lexical Tokens
    IDENTIFIER = auto()
    NUMBER = auto()
    STRING = auto()
    OP = auto()
    DELIMITER = auto()
    INDENT = auto()
    DEDENT = auto()
    NEWLINE = auto()
    COMMENT = auto()
    EOF = auto()

    # Radical Custom Operators
    PIPE = auto()             # |>
    SAFE_DOT = auto()         # ?.
    SAFE_BRACKET = auto()     # ?[
    SAFE_CALL = auto()        # ?.(
    COALESCE = auto()         # ??
    COALESCE_ASSIGN = auto()  # ??=
    ARROW = auto()            # =>
    RANGE_INCLUSIVE = auto()  # ..=
    RANGE_EXCLUSIVE = auto()  # ..
    QUESTION = auto()         # ? (try/error unwrap)

    # Radical & Mojo Keywords
    KW_CONST = auto()         # const
    KW_DEFER = auto()         # defer
    KW_STRUCT = auto()        # struct
    KW_RAW = auto()           # raw
    KW_PARALLEL = auto()      # parallel
    KW_FN = auto()            # fn (strict Mojo-style function)
    KW_GPU = auto()           # gpu (no-cuda GPU kernel / loop)
    KW_LET = auto()           # let (mutable binding)
    KW_USING = auto()         # using (deterministic scoped resource cleanup)
    KW_ENUM = auto()          # enum (algebraic data types / variants)
    KW_UNSAFE = auto()        # unsafe (scoped unchecked low-level access)
    KW_NATIVE = auto()        # native (compiled numerical function tier)
    KW_TRAIT = auto()         # trait (structural protocol / trait)
    KW_SELECT = auto()        # select (channel select block)

    # Contextual Operator
    CARTESIAN_X = auto()      # x in (A x B)


@dataclass(frozen=True)
class Token:
    type: TokenType
    value: str
    line: int
    col: int
    end_line: int = 0
    end_col: int = 0

    def __post_init__(self) -> None:
        if self.end_line == 0:
            object.__setattr__(self, "end_line", self.line)
        if self.end_col == 0:
            object.__setattr__(self, "end_col", self.col + len(self.value))

    def __repr__(self) -> str:
        return f"Token({self.type.name}, {self.value!r}, line={self.line}, col={self.col})"
