import pytest
from radical.exceptions import RadicalCompileError, RadicalSyntaxError


def test_radical_compile_error_formatting():
    err = RadicalCompileError(
        message="Cannot reassign constant 'API_KEY'",
        filename="app.rad",
        lineno=12,
        col_offset=4,
        source_line="    API_KEY = 'new_secret'",
    )

    err_str = str(err)
    assert "RadicalCompileError: Cannot reassign constant 'API_KEY' (app.rad:12:4)" in err_str
    assert "API_KEY = 'new_secret'" in err_str
    assert "^" in err_str


def test_radical_syntax_error_formatting():
    err = RadicalSyntaxError(
        message="Unexpected token '?>'",
        filename="test.rad",
        lineno=1,
        col_offset=5,
    )
    err_str = str(err)
    assert "RadicalSyntaxError: Unexpected token '?>' (test.rad:1:5)" in err_str
