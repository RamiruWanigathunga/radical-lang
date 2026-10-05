import ast
import pytest
from radical.parser import RadicalParser
from radical.semantics import RadicalSemanticAnalyzer
from radical.exceptions import RadicalCompileError


def test_const_valid_declaration():
    parser = RadicalParser()
    source = "const PI = 3.14159\narea = PI * 10 * 10"
    tokens = parser.lexer.tokenize(source)
    transformed, consts = parser.transform_const(tokens)
    result = parser.tokens_to_source(transformed)

    assert "PI = 3.14159" in result

    # Verify semantic analyzer passes
    tree = ast.parse(result)
    analyzer = RadicalSemanticAnalyzer("test.rad")
    for name, line, col in consts:
        analyzer.register_const(name, line, col)
    analyzer.visit(tree)

    locs = {}
    exec(result, locs)
    assert locs["PI"] == 3.14159


def test_const_reassignment_raises_error():
    parser = RadicalParser()
    source = "const API_KEY = 'secret'\nAPI_KEY = 'hacked'"
    tokens = parser.lexer.tokenize(source)
    transformed, consts = parser.transform_const(tokens)
    result = parser.tokens_to_source(transformed)

    tree = ast.parse(result)
    analyzer = RadicalSemanticAnalyzer("app.rad")
    for name, line, col in consts:
        analyzer.register_const(name, line, col)

    with pytest.raises(RadicalCompileError) as exc_info:
        analyzer.visit(tree)

    assert "Cannot reassign constant 'API_KEY'" in str(exc_info.value)


def test_const_aug_assign_raises_error():
    parser = RadicalParser()
    source = "const count = 0\ncount += 1"
    tokens = parser.lexer.tokenize(source)
    transformed, consts = parser.transform_const(tokens)
    result = parser.tokens_to_source(transformed)

    tree = ast.parse(result)
    analyzer = RadicalSemanticAnalyzer("app.rad")
    for name, line, col in consts:
        analyzer.register_const(name, line, col)

    with pytest.raises(RadicalCompileError) as exc_info:
        analyzer.visit(tree)

    assert "Cannot reassign constant 'count'" in str(exc_info.value)


def test_const_for_loop_target_raises_error():
    parser = RadicalParser()
    source = "const i = 100\nfor i in range(5):\n    pass"
    tokens = parser.lexer.tokenize(source)
    transformed, consts = parser.transform_const(tokens)
    result = parser.tokens_to_source(transformed)

    tree = ast.parse(result)
    analyzer = RadicalSemanticAnalyzer("app.rad")
    for name, line, col in consts:
        analyzer.register_const(name, line, col)

    with pytest.raises(RadicalCompileError) as exc_info:
        analyzer.visit(tree)

    assert "Cannot reassign constant 'i'" in str(exc_info.value)
