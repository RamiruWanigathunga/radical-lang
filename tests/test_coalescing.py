import pytest
from radical.parser import RadicalParser
from radical.runtime import _rad_coalesce


def test_coalesce_simple_null():
    parser = RadicalParser()
    source = "val = None ?? 'fallback'"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_coalescing(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {"_rad_coalesce": _rad_coalesce}
    exec(result, locs)
    assert locs["val"] == "fallback"


def test_coalesce_preserves_falsy():
    parser = RadicalParser()
    source = """
a = 0 ?? 42
b = False ?? True
c = "" ?? "non-empty"
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_coalescing(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {"_rad_coalesce": _rad_coalesce}
    exec(result, locs)
    assert locs["a"] == 0
    assert locs["b"] is False
    assert locs["c"] == ""


def test_coalesce_chaining():
    parser = RadicalParser()
    source = "val = None ?? None ?? 'final'"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_coalescing(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {"_rad_coalesce": _rad_coalesce}
    exec(result, locs)
    assert locs["val"] == "final"


def test_coalesce_assign():
    parser = RadicalParser()
    source = """
x = None
x ??= 100
y = 42
y ??= 999
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_coalescing(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {"_rad_coalesce": _rad_coalesce}
    exec(result, locs)
    assert locs["x"] == 100
    assert locs["y"] == 42
