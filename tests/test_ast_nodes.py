"""
Unit tests for radical.ast_nodes.
"""

from radical.ast_nodes import (
    RangeExpr,
    CoalesceExpr,
    SafeAttrExpr,
    SafeIndexExpr,
    SafeCallExpr,
    ArrowFunctionExpr,
    PipeExpr,
    CopyWithExpr,
    TaggedTemplateExpr,
    TryOperatorExpr,
    SIMDVectorExpr,
    ConstDeclStmt,
    LetDeclStmt,
    DestructureStmt,
    StructDefStmt,
    StructField,
    TraitDefStmt,
    EnumDefStmt,
    EnumVariant,
    NativeFnDefStmt,
    CartesianLoopStmt,
    ParallelLoopStmt,
    GPUForStmt,
    DeferStmt,
    UsingStmt,
    UnsafeBlockStmt,
    SelectStmt,
    SelectCase,
    RawBufferStmt,
)


def test_expression_ast_nodes():
    rng = RangeExpr(start=0, end=10, inclusive=True)
    assert rng.start == 0 and rng.end == 10 and rng.inclusive is True

    coal = CoalesceExpr(left="a", right="b")
    assert coal.left == "a" and coal.right == "b"

    safe_attr = SafeAttrExpr(value="obj", attr="prop")
    assert safe_attr.attr == "prop"

    cw = CopyWithExpr(target="pt", updates={"x": 10.0})
    assert cw.updates["x"] == 10.0

    tag = TaggedTemplateExpr(tag="sql", template="SELECT *")
    assert tag.tag == "sql"

    try_op = TryOperatorExpr(expr="fetch()")
    assert try_op.expr == "fetch()"

    simd_node = SIMDVectorExpr(dtype="float32", lanes=[1.0, 2.0, 3.0, 4.0])
    assert len(simd_node.lanes) == 4


def test_statement_ast_nodes():
    let_stmt = LetDeclStmt(target="count", value=0)
    assert let_stmt.target == "count" and let_stmt.value == 0

    const_stmt = ConstDeclStmt(target="MAX", value=100)
    assert const_stmt.target == "MAX" and const_stmt.value == 100

    struct_stmt = StructDefStmt(
        name="User",
        fields=[StructField(name="id", type_annotation="int"), StructField(name="name", type_annotation="str")],
    )
    assert struct_stmt.name == "User"
    assert len(struct_stmt.fields) == 2

    enum_stmt = EnumDefStmt(
        name="Option",
        variants=[EnumVariant(name="Some", fields=[StructField(name="val")]), EnumVariant(name="None")],
    )
    assert len(enum_stmt.variants) == 2

    native_fn = NativeFnDefStmt(
        name="fast_add",
        args=[("a", "f32"), ("b", "f32")],
        return_type="f32",
    )
    assert native_fn.name == "fast_add"

    gpu_loop = GPUForStmt(target="i", start=0, end=1000)
    assert gpu_loop.target == "i"

    sel = SelectStmt(cases=[SelectCase(target_var="msg", channel_recv_expr="ch.recv()")], default_body=["pass"])
    assert len(sel.cases) == 1
    assert sel.default_body == ["pass"]
