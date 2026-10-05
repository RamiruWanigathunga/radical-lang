import pytest
from radical.lexer import RadicalLexer
from radical.token import TokenType


def test_lex_custom_operators():
    source = "data |> clean ?? default_val"
    lexer = RadicalLexer()
    tokens = lexer.tokenize(source)

    types = [t.type for t in tokens if t.type != TokenType.NEWLINE and t.type != TokenType.EOF]
    assert types == [
        TokenType.IDENTIFIER,
        TokenType.PIPE,
        TokenType.IDENTIFIER,
        TokenType.COALESCE,
        TokenType.IDENTIFIER,
    ]
    assert tokens[1].value == "|>"
    assert tokens[3].value == "??"


def test_lex_safe_navigation():
    source = "user?.profile?[0]?.getName?.()"
    lexer = RadicalLexer()
    tokens = lexer.tokenize(source)

    values = [t.value for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
    assert values == ["user", "?.", "profile", "?[", "0", "]", "?.", "getName", "?.(", ")"]


def test_lex_coalesce_assignment():
    source = "x ??= 10"
    lexer = RadicalLexer()
    tokens = lexer.tokenize(source)

    types = [t.type for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
    assert types == [TokenType.IDENTIFIER, TokenType.COALESCE_ASSIGN, TokenType.NUMBER]
    assert tokens[1].value == "??="


def test_lex_arrow_function():
    source = "(x, y) => x + y"
    lexer = RadicalLexer()
    tokens = lexer.tokenize(source)

    values = [t.value for t in tokens if t.type not in (TokenType.NEWLINE, TokenType.EOF)]
    assert "=>" in values
    arrow_tok = next(t for t in tokens if t.type == TokenType.ARROW)
    assert arrow_tok.value == "=>"


def test_lex_ranges():
    source = "0..10 and 1..=5 and a..b and x..=y"
    lexer = RadicalLexer()
    tokens = lexer.tokenize(source)

    range_tokens = [(t.type, t.value) for t in tokens if t.type in (TokenType.RANGE_EXCLUSIVE, TokenType.RANGE_INCLUSIVE)]
    assert range_tokens == [
        (TokenType.RANGE_EXCLUSIVE, ".."),
        (TokenType.RANGE_INCLUSIVE, "..="),
        (TokenType.RANGE_EXCLUSIVE, ".."),
        (TokenType.RANGE_INCLUSIVE, "..="),
    ]


def test_lex_keywords():
    source = "const x = 1\ndefer f.close()\nstruct Point(x: int)\nraw buf[100]:\nparallel for item in items:"
    lexer = RadicalLexer()
    tokens = lexer.tokenize(source)

    kw_tokens = [t.type for t in tokens if t.type in (
        TokenType.KW_CONST, TokenType.KW_DEFER, TokenType.KW_STRUCT, TokenType.KW_RAW, TokenType.KW_PARALLEL
    )]
    assert kw_tokens == [
        TokenType.KW_CONST,
        TokenType.KW_DEFER,
        TokenType.KW_STRUCT,
        TokenType.KW_RAW,
        TokenType.KW_PARALLEL,
    ]


def test_lex_string_and_comment_integrity():
    source = '# This is a comment with |> and ??\nmsg = "String with |> and => and ?."'
    lexer = RadicalLexer()
    tokens = lexer.tokenize(source)

    # String must be preserved intact without splitting
    str_tok = next(t for t in tokens if t.type == TokenType.STRING)
    assert str_tok.value == '"String with |> and => and ?."'

    # Comment must be preserved
    comment_tok = next(t for t in tokens if t.type == TokenType.COMMENT)
    assert comment_tok.value == '# This is a comment with |> and ??'
