import pytest
from radical.parser import RadicalParser
from radical.runtime import _RadicalDeferStack


def test_defer_lifo_execution():
    parser = RadicalParser()
    source = """
log = []
def run_work():
    log.append('start')
    defer log.append('cleanup 1')
    defer log.append('cleanup 2')
    log.append('end')
    return 100

res = run_work()
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_defer(tokens)
    result = parser.tokens_to_source(tokens)

    assert req is True
    assert "_RadicalDeferStack" in result

    locs = {"_RadicalDeferStack": _RadicalDeferStack}
    exec(result, locs)
    assert locs["res"] == 100
    assert locs["log"] == ["start", "end", "cleanup 2", "cleanup 1"]


def test_defer_runs_on_exception():
    parser = RadicalParser()
    source = """
log = []
def faulty():
    defer log.append('always cleaned')
    log.append('before error')
    raise ValueError('oops')

try:
    faulty()
except ValueError:
    pass
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_defer(tokens)
    result = parser.tokens_to_source(tokens)

    locs = {"_RadicalDeferStack": _RadicalDeferStack}
    exec(result, locs)
    assert locs["log"] == ["before error", "always cleaned"]
