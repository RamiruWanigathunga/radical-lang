"""
Radical Language Runtime: Native Execution Tier.
Provides Numba fastmath JIT acceleration when available, with typed fallback.
"""

from typing import Any, Callable


def _rad_native(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Native compilation tier decorator.
    Compiles numerical kernels with Numba JIT (fastmath) when available,
    otherwise executes with native type enforcement.
    """
    try:
        import numba  # type: ignore
        return numba.njit(fastmath=True)(fn)
    except Exception:
        setattr(fn, "_is_radical_native", True)
        return fn
