"""
Radical Language Runtime: Concurrency Channels and Select.
Go-style typed communication channels and non-blocking select blocks.
"""

import queue
from typing import Any, Callable, Optional


class Channel:
    """
    Go-style typed thread-safe communication channel.
    """
    def __init__(self, capacity: int = 0) -> None:
        self.capacity = capacity
        # Go unbuffered channel (capacity 0) has size 1 for synchronization
        self._q: queue.Queue = queue.Queue(maxsize=max(1, capacity) if capacity > 0 else 1)
        self._closed = False

    def send(self, value: Any, timeout: Optional[float] = None) -> bool:
        if self._closed:
            raise RuntimeError("Cannot send on closed channel")
        self._q.put(value, timeout=timeout)
        return True

    def recv(self, timeout: Optional[float] = None) -> Any:
        try:
            return self._q.get(timeout=timeout)
        except queue.Empty:
            return None

    def try_recv(self) -> tuple[bool, Any]:
        try:
            return True, self._q.get_nowait()
        except queue.Empty:
            return False, None

    def close(self) -> None:
        self._closed = True

    def qsize(self) -> int:
        return self._q.qsize()

    def empty(self) -> bool:
        return self._q.empty()

    def __iter__(self):
        while not self._closed or not self._q.empty():
            try:
                yield self._q.get(timeout=0.05)
            except queue.Empty:
                if self._closed:
                    break


class _ChanFactory:
    """Provides `chan[T](capacity)` and `chan(capacity)` syntax."""
    def __getitem__(self, dtype: Any) -> Callable[..., Channel]:
        def creator(capacity: int = 0) -> Channel:
            return Channel(capacity=capacity)
        return creator

    def __call__(self, capacity: int = 0) -> Channel:
        return Channel(capacity=capacity)


chan = _ChanFactory()


def select(*cases: Callable[[], Any], default: Optional[Callable[[], Any]] = None) -> Any:
    """Executes the first available non-blocking channel operation or fallback."""
    for case in cases:
        try:
            res = case()
            if res is not None:
                return res
        except Exception:
            pass
    if default is not None:
        return default()
    return None
