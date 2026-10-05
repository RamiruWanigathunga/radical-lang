import pytest
from radical.parser import RadicalParser
from radical.exceptions import RadicalCompileError


def test_valid_fn_declaration():
    parser = RadicalParser()
    source = """
fn compute_energy(mass: float, c: float = 3e8) -> float:
    return mass * (c ** 2)

e = compute_energy(2.0)
"""
    tokens = parser.lexer.tokenize(source)
    tokens, borrowed = parser.transform_fn_functions(tokens)
    result = parser.tokens_to_source(tokens)

    assert "def compute_energy" in result
    locs = {}
    exec(result, locs)
    assert locs["e"] == 2.0 * (3e8 ** 2)
    assert len(borrowed) == 2


def test_fn_missing_type_annotation_raises():
    parser = RadicalParser()
    source = """
fn add(a: int, b) -> int:
    return a + b
"""
    tokens = parser.lexer.tokenize(source)
    with pytest.raises(RadicalCompileError) as exc_info:
        parser.transform_fn_functions(tokens)

    assert "parameter 'b' is missing a type" in str(exc_info.value)
