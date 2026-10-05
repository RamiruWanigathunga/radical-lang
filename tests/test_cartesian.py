import itertools
import pytest
from radical.parser import RadicalParser


def test_cartesian_2d_with_ranges():
    parser = RadicalParser()
    source = """
pairs = []
for x, y in (0..2 x 1..=2):
    pairs.append((x, y))
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_cartesian_loops(tokens)
    tokens = parser.transform_ranges(tokens)
    result = parser.tokens_to_source(tokens)

    assert req is True
    assert "itertools.product" in result

    locs = {"itertools": itertools}
    exec(result, locs)
    assert locs["pairs"] == [(0, 1), (0, 2), (1, 1), (1, 2)]


def test_cartesian_3d_with_lists():
    parser = RadicalParser()
    source = """
triplets = []
for a, b, c in ([1, 2] x ['x', 'y'] x [True, False]):
    triplets.append((a, b, c))
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_cartesian_loops(tokens)
    result = parser.tokens_to_source(tokens)

    assert req is True
    assert "itertools.product" in result

    locs = {"itertools": itertools}
    exec(result, locs)
    expected = list(itertools.product([1, 2], ['x', 'y'], [True, False]))
    assert locs["triplets"] == expected
