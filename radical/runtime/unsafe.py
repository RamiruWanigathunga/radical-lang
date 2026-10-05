"""
Radical Language Runtime: Scoped Unsafe Execution Context.
Tracks unsafe block depth per thread to guard raw pointer operations.
"""

import threading
from typing import Any


_unsafe_thread_state = threading.local()


class _RadicalUnsafeContext:
    def __enter__(self) -> "_RadicalUnsafeContext":
        _unsafe_thread_state.depth = getattr(_unsafe_thread_state, "depth", 0) + 1
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        current = getattr(_unsafe_thread_state, "depth", 1)
        _unsafe_thread_state.depth = max(0, current - 1)


def _rad_unsafe_context() -> _RadicalUnsafeContext:
    return _RadicalUnsafeContext()


def _rad_is_unsafe_active() -> bool:
    return getattr(_unsafe_thread_state, "depth", 0) > 0
