import pytest
from radical.parser import RadicalParser
from radical.runtime import _rad_safe_attr, _rad_safe_item, _rad_safe_call


def test_safe_attribute_access():
    parser = RadicalParser()
    source = "val = user?.profile?.name"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_safe_nav(tokens)
    result = parser.tokens_to_source(transformed)

    assert "_rad_safe_attr" in result

    # Test with None
    locs = {"user": None, "_rad_safe_attr": _rad_safe_attr}
    exec(result, locs)
    assert locs["val"] is None

    # Test with real object
    class Profile:
        name = "Bob"
    class User:
        profile = Profile()

    locs = {"user": User(), "_rad_safe_attr": _rad_safe_attr}
    exec(result, locs)
    assert locs["val"] == "Bob"


def test_safe_indexing():
    parser = RadicalParser()
    source = "item = data?[0]?[1]"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_safe_nav(tokens)
    result = parser.tokens_to_source(transformed)

    assert "_rad_safe_item" in result

    # Test with None
    locs = {"data": None, "_rad_safe_item": _rad_safe_item}
    exec(result, locs)
    assert locs["item"] is None

    # Test with out of bounds
    locs = {"data": [[10]], "_rad_safe_item": _rad_safe_item}
    exec(result, locs)
    assert locs["item"] is None

    # Test with present data
    locs = {"data": [[10, 20]], "_rad_safe_item": _rad_safe_item}
    exec(result, locs)
    assert locs["item"] == 20


def test_safe_call():
    parser = RadicalParser()
    source = "res = callback?.('arg1', 'arg2')"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_safe_nav(tokens)
    result = parser.tokens_to_source(transformed)

    assert "_rad_safe_call" in result

    # Test with None
    locs = {"callback": None, "_rad_safe_call": _rad_safe_call}
    exec(result, locs)
    assert locs["res"] is None

    # Test with real function
    def add(a, b):
        return f"{a}+{b}"
    locs = {"callback": add, "_rad_safe_call": _rad_safe_call}
    exec(result, locs)
    assert locs["res"] == "arg1+arg2"
