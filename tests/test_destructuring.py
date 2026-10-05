import pytest
from radical.parser import RadicalParser


def test_dict_destructuring():
    parser = RadicalParser()
    source = """
user = {"id": 101, "name": "Alice", "role": "admin"}
{ id, name } = user
"""
    tokens = parser.lexer.tokenize(source)
    tokens, _ = parser.transform_destructuring(tokens)
    result = parser.tokens_to_source(tokens)

    locs = {}
    exec(result, locs)
    assert locs["id"] == 101
    assert locs["name"] == "Alice"


def test_object_destructuring():
    parser = RadicalParser()
    source = """
class ServerConfig:
    host = "localhost"
    port = 8080

config = ServerConfig()
{ host, port } = config
"""
    tokens = parser.lexer.tokenize(source)
    tokens, _ = parser.transform_destructuring(tokens)
    result = parser.tokens_to_source(tokens)

    locs = {}
    exec(result, locs)
    assert locs["host"] == "localhost"
    assert locs["port"] == 8080


def test_const_destructuring():
    parser = RadicalParser()
    source = """
res = {"token": "secret_jwt", "status": 200}
const { token, status } = res
"""
    tokens = parser.lexer.tokenize(source)
    tokens, consts = parser.transform_destructuring(tokens)
    result = parser.tokens_to_source(tokens)

    assert ("token", 3, 0) in [(c[0], c[1], 0) for c in consts]
    assert ("status", 3, 0) in [(c[0], c[1], 0) for c in consts]

    locs = {}
    exec(result, locs)
    assert locs["token"] == "secret_jwt"
    assert locs["status"] == 200
