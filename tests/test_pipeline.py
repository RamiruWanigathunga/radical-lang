import pytest
from radical.parser import RadicalParser


def test_pipeline_simple():
    parser = RadicalParser()
    source = "res = '  hello  ' |> str.strip |> str.upper"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {}
    exec(result, locs)
    assert locs["res"] == "HELLO"


def test_pipeline_with_args():
    parser = RadicalParser()
    source = "res = 5 |> pow(2)"
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {}
    exec(result, locs)
    assert locs["res"] == 25  # pow(5, 2)


def test_pipeline_with_placeholder():
    parser = RadicalParser()
    # Subtract 10 from 100: 10 |> (lambda a, b: a - b)(100, _)
    source = """
def sub(a, b):
    return a - b
res = 10 |> sub(100, _)
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {}
    exec(result, locs)
    assert locs["res"] == 90  # sub(100, 10)


def test_multiline_pipeline():
    parser = RadicalParser()
    source = """
data = [1, 2, 3]
res = data |>
    sum |>
    str
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {}
    exec(result, locs)
    assert locs["res"] == "6"


def test_pipeline_fusion_filter_map_list():
    parser = RadicalParser()
    source = """
data = [1, 2, 3, 4, 5, 6]
is_even = lambda x: x % 2 == 0
square = lambda x: x * x
res = data |> filter(is_even, _) |> map(square, _) |> list
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    assert "for _rad_x" in result
    assert "if is_even(" in result

    locs = {}
    exec(result, locs)
    assert locs["res"] == [4, 16, 36]


def test_pipeline_fusion_map_list():
    parser = RadicalParser()
    source = """
data = [1, 2, 3]
square = lambda x: x * x
res = data |> map(square) |> list
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    assert "for _rad_x" in result
    locs = {}
    exec(result, locs)
    assert locs["res"] == [1, 4, 9]


def test_pipeline_fusion_filter_list():
    parser = RadicalParser()
    source = """
data = [1, 2, 3, 4]
is_even = lambda x: x % 2 == 0
res = data |> filter(is_even) |> list
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    assert "for _rad_x" in result
    locs = {}
    exec(result, locs)
    assert locs["res"] == [2, 4]


def test_pipeline_fusion_collector_sum():
    parser = RadicalParser()
    source = """
data = [1, 2, 3, 4]
is_even = lambda x: x % 2 == 0
square = lambda x: x * x
res = data |> filter(is_even) |> map(square) |> sum
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    assert "sum(" in result
    locs = {}
    exec(result, locs)
    assert locs["res"] == 20  # 4 + 16


def test_pipeline_fusion_set():
    parser = RadicalParser()
    source = """
data = [1, 2, 2, 3]
square = lambda x: x * x
res = data |> map(square) |> set
"""
    tokens = parser.lexer.tokenize(source)
    transformed = parser.transform_pipelines(tokens)
    result = parser.tokens_to_source(transformed)

    locs = {}
    exec(result, locs)
    assert locs["res"] == {1, 4, 9}


def test_pipeline_fusion_with_arrows():
    from radical.transformer import RadicalTranspiler
    transpiler = RadicalTranspiler()
    source = """
data = [1, 2, 3, 4, 5]
res = data |> filter((x) => x > 2) |> map((x) => x * 10) |> list
"""
    py_code = transpiler.transpile(source)
    locs = {}
    exec(py_code, locs)
    assert locs["res"] == [30, 40, 50]

