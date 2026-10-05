"""
Radical Language Runtime: Deferred Execution.
Provides LIFO cleanup stack for defer statements.
"""

from typing import Any, Callable


class _RadicalDeferStack:
    """
    Manages deferred execution tasks in LIFO (Last-In, First-Out) order.
    """
    def __init__(self) -> None:
        self._actions: list[Callable[[], Any]] = []

    def defer(self, action: Callable[[], Any]) -> None:
        self._actions.append(action)

    def execute_all(self) -> None:
        exceptions: list[Exception] = []
        while self._actions:
            action = self._actions.pop()
            try:
                action()
            except Exception as e:
                exceptions.append(e)
        if exceptions:
            # Raise the first exception encountered if any
            raise exceptions[0]

    def __enter__(self) -> "_RadicalDeferStack":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.execute_all()
