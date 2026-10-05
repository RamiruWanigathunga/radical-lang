import pytest
from radical.parser import RadicalParser


def test_arrow_multi_param():
    parser = RadicalParser()
    source = "add = (a, b) => a + b"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_arrows(tokens)
    result = parser.tokens_to_source(transformed)

    assert "lambda" in result
    locs = {}
    exec(result, locs)
    assert locs["add"](10, 20) == 30


def test_arrow_single_param():
    parser = RadicalParser()
    source = "double = x => x * 2"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_arrows(tokens)
    result = parser.tokens_to_source(transformed)

    assert "lambda" in result
    locs = {}
    exec(result, locs)
    assert locs["double"](7) == 14


def test_arrow_zero_params():
    parser = RadicalParser()
    source = "get_magic = () => 42"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_arrows(tokens)
    result = parser.tokens_to_source(transformed)

    assert "lambda" in result
    locs = {}
    exec(result, locs)
    assert locs["get_magic"]() == 42


def test_arrow_with_type_annotations():
    parser = RadicalParser()
    source = "greet = (name: str, count: int) => name * count"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_arrows(tokens)
    result = parser.tokens_to_source(transformed)

    assert "lambda" in result
    locs = {}
    exec(result, locs)
    assert locs["greet"]("Hi!", 3) == "Hi!Hi!Hi!"
