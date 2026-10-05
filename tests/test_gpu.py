import pytest
from radical.parser import RadicalParser
from radical.gpu import gpu


def test_gpu_for_loop_syntax():
    parser = RadicalParser()
    source = """
n = 100
a = gpu.alloc(n, 'float32', [1.0] * n)
b = gpu.alloc(n, 'float32', [2.0] * n)
out = gpu.alloc(n, 'float32')

gpu for i in 0..n:
    out[i] = a[i] * 3.0 + b[i]
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_gpu_constructs(tokens)
    tokens = parser.transform_ranges(tokens)
    result = parser.tokens_to_source(tokens)

    assert req is True
    assert "gpu.execute_loop" in result

    locs = {"gpu": gpu}
    exec(result, locs)
    out = locs["out"]
    assert out[0] == 5.0
    assert out[99] == 5.0


def test_gpu_fn_kernel_syntax():
    parser = RadicalParser()
    source = """
gpu fn vector_scaled_add(a: list, b: list, scale: float) -> list:
    res = []
    for x, y in zip(a, b):
        res.append(x + y * scale)
    return res

ans = vector_scaled_add([1, 2], [10, 20], 2.0)
"""
    tokens = parser.lexer.tokenize(source)
    tokens, _ = parser.transform_gpu_constructs(tokens)
    tokens, _ = parser.transform_fn_functions(tokens)
    result = parser.tokens_to_source(tokens)

    assert "def vector_scaled_add" in result

    locs = {}
    exec(result, locs)
    assert locs["ans"] == [21.0, 42.0]
