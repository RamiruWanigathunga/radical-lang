from dataclasses import dataclass, FrozenInstanceError
import typing
import pytest
from radical.parser import RadicalParser


def test_single_line_struct():
    parser = RadicalParser()
    source = "struct Point(x: float, y: float)"
    tokens = parser.lexer.tokenize(source)
    transformed, req = parser.transform_structs(tokens)
    result = parser.tokens_to_source(transformed)

    assert req is True
    assert "@dataclass" in result and "slots" in result and "frozen" in result
    assert "class Point:" in result

    locs = {"dataclass": dataclass, "typing": typing}
    exec(result, locs)
    Point = locs["Point"]
    p = Point(1.5, 2.5)
    assert p.x == 1.5
    assert p.y == 2.5

    # Verify immutability
    with pytest.raises(FrozenInstanceError):
        p.x = 10.0


def test_struct_with_defaults():
    parser = RadicalParser()
    source = "struct Color(r: int = 255, g: int = 0, b: int = 0)"
    tokens = parser.lexer.tokenize(source)
    transformed, _ = parser.transform_structs(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {"dataclass": dataclass, "typing": typing}
    exec(result, locs)
    Color = locs["Color"]
    c = Color()
    assert c.r == 255
    assert c.g == 0
    assert c.b == 0


def test_multiline_struct_with_method():
    parser = RadicalParser()
    source = """
struct Vector:
    x: float
    y: float
    def norm(self) -> float:
        return (self.x**2 + self.y**2) ** 0.5
"""
    tokens = parser.lexer.tokenize(source)
    transformed, _ = parser.transform_structs(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {"dataclass": dataclass, "typing": typing}
    exec(result, locs)
    Vector = locs["Vector"]
    v = Vector(3.0, 4.0)
    assert v.norm() == 5.0
