"""
Radical Language Runtime: Safe Navigation and Coalescing.
Implements safe attribute traversal (?.), safe item access (?[), safe calls (?.()),
and nullish coalescing (??, ??=).
"""

from typing import Any


def _rad_safe_attr(obj: Any, attr: str) -> Any:
    """
    Safely access an attribute on obj.
    Returns None if obj is None or if attr does not exist.
    """
    if obj is None:
        return None
    return getattr(obj, attr, None)


def _rad_safe_item(obj: Any, key: Any) -> Any:
    """
    Safely access an index or key on obj.
    Returns None if obj is None or if the index/key is out of bounds / missing.
    """
    if obj is None:
        return None
    if obj.__class__ is dict:
        return obj.get(key)
    if isinstance(obj, dict):
        return obj.get(key)
    if obj.__class__ is list or obj.__class__ is tuple:
        return obj[key] if isinstance(key, int) and -len(obj) <= key < len(obj) else None
    try:
        return obj[key]
    except (IndexError, KeyError, TypeError):
        return None


def _rad_safe_call(fn: Any, *args: Any, **kwargs: Any) -> Any:
    """
    Safely call fn if callable and not None.
    Returns None if fn is None.
    """
    if fn is None:
        return None
    if not callable(fn):
        return None
    return fn(*args, **kwargs)


def _rad_coalesce(val: Any, fallback: Any) -> Any:
    """
    Nullish coalescing operator implementation.
    Returns val if val is not None; otherwise returns fallback (or fallback() if callable).
    Preserves falsy values like 0, False, and empty strings.
    """
    if val is not None:
        return val
    if callable(fallback):
        return fallback()
    return fallback
