"""
Radical Language Exceptions.
Provides structured compile-time and runtime error classes with line/column tracking.
"""

from typing import Optional


class RadicalError(Exception):
    """Base exception for all Radical errors."""
    pass


import os


class RadicalCompileError(RadicalError):
    """
    Raised when a compile-time invariant (e.g., const reassignment) is violated.
    """
    def __init__(
        self,
        message: str,
        filename: Optional[str] = None,
        lineno: Optional[int] = None,
        col_offset: Optional[int] = None,
        source_line: Optional[str] = None,
        hint: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.filename = filename or "<unknown>"
        self.lineno = lineno
        self.col_offset = col_offset
        self.source_line = source_line
        self.hint = hint

    def __str__(self) -> str:
        loc_parts = [self.filename]
        if self.lineno is not None:
            loc_parts.append(str(self.lineno))
            if self.col_offset is not None:
                loc_parts.append(str(self.col_offset))
        loc_str = ":".join(loc_parts)

        s_line = self.source_line
        if s_line is None and self.filename and os.path.exists(self.filename) and self.lineno:
            try:
                with open(self.filename, "r", encoding="utf-8") as f:
                    lines = f.readlines()
                    if 1 <= self.lineno <= len(lines):
                        s_line = lines[self.lineno - 1].rstrip("\r\n")
            except Exception:
                pass

        msg = f"RadicalCompileError: {self.message} ({loc_str})"
        if s_line:
            msg += f"\n  {s_line.strip()}"
            if self.col_offset is not None and self.col_offset > 0:
                indent = " " * (self.col_offset + 1)
                caret_line = f"{indent}^"
                if self.hint:
                    caret_line += f" ({self.hint})"
                msg += f"\n{caret_line}"
            elif self.hint:
                msg += f"\n  --> Hint: {self.hint}"
        return msg


class RadicalSyntaxError(RadicalCompileError):
    """Raised when Radical encounters invalid syntax during lexing or parsing."""
    def __str__(self) -> str:
        base = super().__str__()
        return base.replace("RadicalCompileError:", "RadicalSyntaxError:", 1)
