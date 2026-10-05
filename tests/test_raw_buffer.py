import ctypes
import pytest
from radical.parser import RadicalParser


def test_raw_buffer_default_uint8():
    parser = RadicalParser()
    source = """
raw buf[1024]:
    buf[0] = 0xAA
    buf[1023] = 0xFF
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_raw_buffers(tokens)
    result = parser.tokens_to_source(tokens)

    assert req is True
    assert "ctypes.c_uint8 * 1024" in result

    locs = {"ctypes": ctypes}
    exec(result, locs)
    buf = locs["buf"]
    assert len(buf) == 1024
    assert buf[0] == 0xAA
    assert buf[1023] == 0xFF


def test_raw_buffer_with_dtype():
    parser = RadicalParser()
    source = """
raw fbuf[16, c_float]:
    fbuf[0] = 3.14
"""
    tokens = parser.lexer.tokenize(source)
    tokens, req = parser.transform_raw_buffers(tokens)
    result = parser.tokens_to_source(tokens)

    assert req is True
    assert "ctypes.c_float * 16" in result

    locs = {"ctypes": ctypes}
    exec(result, locs)
    fbuf = locs["fbuf"]
    assert len(fbuf) == 16
    assert abs(fbuf[0] - 3.14) < 1e-5
