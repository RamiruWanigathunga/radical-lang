"""
Radical Language Runtime: Parallel Execution Engine.
Dispatches iterations across multi-core CPU threads or processes.
"""

import os
import sys
import concurrent.futures
from typing import Any, Callable, Optional


def _rad_parallel_for(
    iterable: Any,
    fn: Callable[[Any], Any],
    threads: Optional[int] = None,
    chunk_size: Optional[int] = None,
    mode: str = "thread",
) -> list[Any]:
    """
    Executes a loop over iterable across multiple worker threads or processes.
    - mode="thread": Uses ThreadPoolExecutor (shared memory).
    - mode="process": Uses forked process pool (bypasses GIL for 100% CPU multi-core utilization).
    """
    workers = threads or min(32, (os.cpu_count() or 4))
    if not isinstance(iterable, (list, tuple, range)):
        items = list(iterable)
    else:
        items = iterable
    n = len(items)
    if n == 0:
        return []

    actual_chunk = chunk_size or max(1, n // (workers * 4))

    # Fork is supported on POSIX systems (Linux & macOS) for clean CPU multi-core scaling
    is_safe_to_fork = hasattr(os, "fork")
    if mode in ("process", "fork", "multiprocess") and is_safe_to_fork:
        try:
            fn_name = getattr(fn, "__name__", None)
            if fn_name == "<lambda>":
                _lid = getattr(_rad_parallel_for, "_lid", 0) + 1
                _rad_parallel_for._lid = _lid
                fn_name = f"_rad_anon_worker_{_lid}"
                fn.__name__ = fn_name
                fn.__qualname__ = fn_name

            if fn_name:
                mod_name = getattr(fn, "__module__", None)
                if mod_name and mod_name in sys.modules:
                    setattr(sys.modules[mod_name], fn_name, fn)
                main_mod = sys.modules.get("__main__")
                if main_mod and not hasattr(main_mod, fn_name):
                    setattr(main_mod, fn_name, fn)

            import multiprocessing
            ctx = multiprocessing.get_context("fork")
            with ctx.Pool(processes=workers) as pool:
                return pool.map(fn, items, chunksize=actual_chunk)
        except Exception:
            pass

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        return list(executor.map(fn, items, chunksize=actual_chunk))
