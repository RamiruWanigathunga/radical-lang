import pytest
from radical.parser import RadicalParser


def test_transform_range_exclusive():
    parser = RadicalParser()
    source = "r = 0..10"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_ranges(tokens)
    result = parser.tokens_to_source(transformed)
    assert "r = range(0, 10)" in result

    # Test evaluation
    locs = {}
    exec(result, locs)
    assert list(locs["r"]) == list(range(0, 10))


def test_transform_range_inclusive():
    parser = RadicalParser()
    source = "r = 1..=5"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_ranges(tokens)
    result = parser.tokens_to_source(transformed)
    assert "range(1, (5) + 1)" in result

    # Test evaluation
    locs = {}
    exec(result, locs)
    assert list(locs["r"]) == [1, 2, 3, 4, 5]


def test_transform_range_stepped():
    parser = RadicalParser()
    source = "r = 0..10..2"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_ranges(tokens)
    result = parser.tokens_to_source(transformed)
    assert "range(0, 10, 2)" in result

    locs = {}
    exec(result, locs)
    assert list(locs["r"]) == [0, 2, 4, 6, 8]


def test_range_in_for_loop():
    parser = RadicalParser()
    source = "nums = []\nfor i in 0..5:\n    nums.append(i)"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_ranges(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {}
    exec(result, locs)
    assert locs["nums"] == [0, 1, 2, 3, 4]


def test_range_with_arithmetic_expressions():
    parser = RadicalParser()
    source = """
W = 10
items1 = [i for i in 2..W - 2]
items2 = [i for i in W - 8..W - 4]
items3 = [i for i in -2..=2]
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_ranges(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {}
    exec(result, locs)
    assert locs["items1"] == [2, 3, 4, 5, 6, 7]
    assert locs["items2"] == [2, 3, 4, 5]
    assert locs["items3"] == [-2, -1, 0, 1, 2]
