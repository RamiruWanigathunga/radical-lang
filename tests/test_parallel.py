import threading
import time
import pytest
from radical.parser import RadicalParser
from radical.runtime import _rad_parallel_for


def test_parallel_for_multi_threading():
    parser = RadicalParser()
    source = """
results = []
lock = threading.Lock()
items = [0.01, 0.01, 0.01, 0.01]
parallel for t in items:
    time.sleep(t)
    with lock:
        results.append(threading.get_ident())
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_parallel_loops(tokens)
    result = parser.tokens_to_source(tokens)

    assert req is True
    assert "_rad_parallel_for" in result

    locs = {"_rad_parallel_for": _rad_parallel_for, "threading": threading, "time": time}
    exec(result, locs)
    # Check that work was distributed across multiple threads
    unique_threads = set(locs["results"])
    assert len(unique_threads) > 1


def test_parallel_for_with_worker_options():
    parser = RadicalParser()
    source = """
squared = []
lock = threading.Lock()
parallel(threads=2) for i in [1, 2, 3, 4]:
    with lock:
        squared.append(i * i)
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_parallel_loops(tokens)
    result = parser.tokens_to_source(tokens)

    assert "threads" in result and "2" in result

    locs = {"_rad_parallel_for": _rad_parallel_for, "threading": threading}
    exec(result, locs)
    assert sorted(locs["squared"]) == [1, 4, 9, 16]


def test_parallel_for_assignment_and_return():
    parser = RadicalParser()
    source = """
squared = parallel for i in [1, 2, 3, 4]:
    return i * i
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_parallel_loops(tokens)
    result = parser.tokens_to_source(tokens)

    assert "squared = _rad_parallel_for" in result
    locs = {"_rad_parallel_for": _rad_parallel_for}
    exec(result, locs)
    assert locs["squared"] == [1, 4, 9, 16]


def test_parallel_for_process_mode():
    parser = RadicalParser()
    source = """
results = parallel(mode="process", threads=2) for i in [10, 20, 30]:
    return i * 2
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_parallel_loops(tokens)
    result = parser.tokens_to_source(tokens)

    locs = {"_rad_parallel_for": _rad_parallel_for}
    exec(result, locs)
    assert locs["results"] == [20, 40, 60]


def test_parallel_list_comprehension():
    parser = RadicalParser()
    source = "doubled = parallel [x * 10 for x in [1, 2, 3, 4]]"
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_parallel_loops(tokens)
    result = parser.tokens_to_source(tokens)

    assert "_rad_parallel_for" in result
    locs = {"_rad_parallel_for": _rad_parallel_for}
    exec(result, locs)
    assert locs["doubled"] == [10, 20, 30, 40]
