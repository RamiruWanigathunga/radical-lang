"""
Radical Language Runtime: Algebraic Data Types.
Functional Result[T, E] and Option[T] implementations.
"""

from typing import Any


class Result:
    """
    Rust-inspired Result type representing either success (Ok) or failure (Err).
    """
    __slots__ = ("_value", "_error", "_is_ok")

    def __init__(self, value: Any = None, error: Any = None, is_ok: bool = True) -> None:
        self._value = value
        self._error = error
        self._is_ok = is_ok

    def is_ok(self) -> bool:
        return self._is_ok

    def is_err(self) -> bool:
        return not self._is_ok

    def __class_getitem__(cls, item: Any) -> Any:
        return cls

    @property
    def value(self) -> Any:
        if not self._is_ok:
            raise RuntimeError(f"Attempted to access .value on Err: {self._error}")
        return self._value

    @property
    def val(self) -> Any:
        return self.value

    @property
    def error(self) -> Any:
        return self._error

    @property
    def err(self) -> Any:
        return self.error

    def unwrap(self) -> Any:
        if not self._is_ok:
            raise RuntimeError(f"Unwrap failed on Err: {self._error}")
        return self._value

    def unwrap_or(self, default: Any) -> Any:
        return self._value if self._is_ok else default

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Result):
            return self._is_ok == other._is_ok and (
                self._value == other._value if self._is_ok else self._error == other._error
            )
        return False

    def __repr__(self) -> str:
        return f"Ok({self._value!r})" if self._is_ok else f"Err({self._error!r})"


def Ok(value: Any = None) -> Result:
    return Result(value=value, error=None, is_ok=True)


def Err(error: Any = None) -> Result:
    return Result(value=None, error=error, is_ok=False)


class Option:
    """
    Rust/Swift-inspired Option type representing either a value (Some) or absence (Nil).
    """
    __slots__ = ("_value", "_is_some")

    def __init__(self, value: Any = None, is_some: bool = True) -> None:
        self._value = value
        self._is_some = is_some

    def is_some(self) -> bool:
        return self._is_some

    def is_none(self) -> bool:
        return not self._is_some

    def __class_getitem__(cls, item: Any) -> Any:
        return cls

    @property
    def value(self) -> Any:
        if not self._is_some:
            raise RuntimeError("Attempted to access .value on Nil/None")
        return self._value

    def unwrap(self) -> Any:
        if not self._is_some:
            raise RuntimeError("Unwrap failed on Nil/None")
        return self._value

    def unwrap_or(self, default: Any) -> Any:
        return self._value if self._is_some else default

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Option):
            return self._is_some == other._is_some and (
                self._value == other._value if self._is_some else True
            )
        return False

    def __repr__(self) -> str:
        return f"Some({self._value!r})" if self._is_some else "Nil"


def Some(value: Any) -> Option:
    return Option(value=value, is_some=True)


Nil = Option(value=None, is_some=False)
None_ = Nil

Result.Ok = staticmethod(Ok)  # type: ignore[attr-defined]
Result.Err = staticmethod(Err)  # type: ignore[attr-defined]
Option.Some = staticmethod(Some)  # type: ignore[attr-defined]
Option.None_ = staticmethod(lambda: Nil)  # type: ignore[attr-defined]
