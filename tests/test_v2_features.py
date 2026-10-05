"""
Tests for Radical v2 language features:
- `let` declarations
- `using` scoped resource management
- `unsafe:` blocks and `buffer[T]` typed memory buffers
- `Result[T, E]`, `Option[T]`, and Rust-style `?` operator
- `enum` ADTs and pattern-matchable variants
- `struct with { ... }` functional copy-update
- `chan[T]` and `select` concurrency primitives
- `native fn` compilation tier
- `radical explain` CLI output
"""

import ctypes
import pytest
from radical.parser import RadicalParser
from radical.transformer import RadicalTranspiler
from radical.runtime import (
    Result, Ok, Err, Option, Some, Nil, None_,
    chan, Channel, select,
    buffer, TypedBuffer, BufferSlice, u8, f16, f32,
    Arena, arena,
    _rad_unsafe_context, _rad_is_unsafe_active,
    _rad_copy_with, _rad_native,
)
from radical.exceptions import RadicalCompileError
from radical.cli import main


def test_let_binding():
    transpiler = RadicalTranspiler()
    source = """
let x = 10
let mut y = 20
let (a, b) = (1, 2)
let z: int = 30
y = y + 5
"""
    py_code = transpiler.transpile(source)
    locs = {}
    exec(py_code, locs)
    assert locs["x"] == 10
    assert locs["y"] == 25
    assert locs["a"] == 1
    assert locs["b"] == 2
    assert locs["z"] == 30


def test_using_resource_management(tmp_path):
    f_path = tmp_path / "test.txt"
    f_path.write_text("hello radical", encoding="utf-8")

    transpiler = RadicalTranspiler()
    source = f"""
read_val = ""
using f = open(r"{f_path}", "r"):
    read_val = f.read()
"""
    py_code = transpiler.transpile(source)
    assert "with open(" in py_code
    assert "as f:" in py_code
    locs = {}
    exec(py_code, locs)
    assert locs["read_val"] == "hello radical"


def test_typed_buffer_safe_access():
    buf = buffer[u8](16)
    assert len(buf) == 16
    assert buf.size == 16
    assert buf.itemsize == 1
    assert buf.nbytes == 16

    buf[0] = 42
    buf[15] = 255
    assert buf[0] == 42
    assert buf[15] == 255

    # Bounds check
    with pytest.raises(IndexError):
        _ = buf[16]
    with pytest.raises(IndexError):
        buf[16] = 10

    # Slicing
    sl = buf[0:5]
    assert len(sl) == 5
    assert sl[0] == 42
    sl[1] = 99
    assert buf[1] == 99


def test_typed_buffer_unsafe_block():
    buf = buffer[u8](8)

    # Outside unsafe block, ptr and unchecked operations must fail
    with pytest.raises(RuntimeError) as exc_info:
        _ = buf.ptr
    assert "inside an 'unsafe:' block" in str(exc_info.value)

    with pytest.raises(RuntimeError):
        buf.write_unchecked(0, 123)

    with pytest.raises(RuntimeError):
        _ = buf.read_unchecked(0)

    # Inside unsafe block, raw pointer and unchecked operations succeed
    with _rad_unsafe_context():
        raw_ptr = buf.ptr
        assert raw_ptr > 0
        buf.write_unchecked(0, 77)
        val = buf.read_unchecked(0)
        assert val == 77

    assert buf[0] == 77


def test_unsafe_block_transpilation():
    transpiler = RadicalTranspiler()
    source = """
buf = buffer[u8](4)
unsafe:
    buf.write_unchecked(0, 88)
val = buf[0]
"""
    py_code = transpiler.transpile(source)
    assert "_rad_unsafe_context()" in py_code
    locs = {}
    exec(py_code, locs)
    assert locs["val"] == 88


def test_result_and_option_runtime():
    ok = Ok(42)
    err = Err("failed")
    assert ok.is_ok() and not ok.is_err()
    assert err.is_err() and not err.is_ok()
    assert ok.unwrap() == 42
    assert err.unwrap_or(0) == 0

    with pytest.raises(RuntimeError):
        err.unwrap()

    some = Some("value")
    nil = Nil
    assert some.is_some() and not some.is_none()
    assert nil.is_none() and not nil.is_some()
    assert some.unwrap() == "value"
    assert nil.unwrap_or("fallback") == "fallback"


def test_try_operator_transpilation():
    transpiler = RadicalTranspiler()
    source = """
fn compute_success(x: int) -> Result:
    return Ok(x * 2)

fn compute_fail(x: int) -> Result:
    return Err("math error")

fn try_pipeline(should_fail: bool) -> Result:
    if should_fail:
        res = compute_fail(10)?
    else:
        res = compute_success(10)?
    return Ok(res + 1)

r1 = try_pipeline(False)
r2 = try_pipeline(True)
"""
    py_code = transpiler.transpile(source)
    assert "_rad_try_tmp" in py_code
    locs = {}
    exec(py_code, locs)
    assert locs["r1"].is_ok()
    assert locs["r1"].unwrap() == 21
    assert locs["r2"].is_err()
    assert locs["r2"].error == "math error"


def test_enum_adt_transpilation():
    transpiler = RadicalTranspiler()
    source = """
enum Status:
    Pending
    Active
    Done

enum Shape:
    Circle(radius: float)
    Rectangle(width: float, height: float)

c = Circle(radius=5.0)
"""
    py_code = transpiler.transpile(source)
    assert "class Status:" in py_code
    assert 'Pending = "Pending"' in py_code
    assert "class Shape:" in py_code
    assert "class Circle(Shape):" in py_code
    assert "class Rectangle(Shape):" in py_code

    locs = {}
    exec(py_code, locs)
    Status = locs["Status"]
    assert Status.Pending == "Pending"
    assert Status.Done == "Done"

    Circle = locs["Circle"]
    c = Circle(radius=5.0)
    assert c.radius == 5.0


def test_struct_copy_with():
    transpiler = RadicalTranspiler()
    source = """
struct Point(x: float, y: float)

p1 = Point(1.0, 2.0)
p2 = p1 with { x: 10.0 }
"""
    py_code = transpiler.transpile(source)
    assert "_rad_copy_with" in py_code
    locs = {}
    exec(py_code, locs)
    p1 = locs["p1"]
    p2 = locs["p2"]
    assert p1.x == 1.0
    assert p1.y == 2.0
    assert p2.x == 10.0
    assert p2.y == 2.0


def test_channels_and_select():
    ch = chan[int](5)
    ch.send(100)
    ch.send(200)

    val1 = ch.recv()
    val2 = ch.recv()
    assert val1 == 100
    assert val2 == 200

    # Select
    def try_case():
        ok, v = ch.try_recv()
        return v if ok else None

    res = select(try_case, default=lambda: "empty")
    assert res == "empty"


def test_native_fn():
    transpiler = RadicalTranspiler()
    source = """
native fn add_fast(a: int, b: int) -> int:
    return a + b

ans = add_fast(3, 7)
"""
    py_code = transpiler.transpile(source)
    assert "@_rad_native" in py_code
    locs = {}
    exec(py_code, locs)
    assert locs["ans"] == 10


def test_cli_explain(tmp_path, capsys):
    src = tmp_path / "pipeline.rad"
    src.write_text("""
let items = [1, 2, 3, 4] |> map(x => x * 2, _) |> list
unsafe:
    b = buffer[u8](10)
""", encoding="utf-8")

    code = main(["explain", str(src)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Radical Optimization & Execution Report" in captured.out
    assert "pipeline fused" in captured.out or "pipeline step" in captured.out
    assert "unsafe block" in captured.out


def test_scoped_memory_arena():
    a = arena(capacity=1024)
    assert a.capacity == 1024
    assert a.used == 0

    buf1 = a.alloc(128, dtype="u8")
    assert len(buf1) == 128
    assert a.used >= 128
    buf1[0] = 55
    assert buf1[0] == 55

    buf2 = a.alloc(64, dtype="f32")
    assert len(buf2) == 64
    buf2[0] = 3.14
    assert abs(buf2[0] - 3.14) < 1e-5

    # Test O(1) reset
    a.reset()
    assert a.used == 0

    # Test out of memory
    with pytest.raises(MemoryError):
        a.alloc(2000)

    # Test using context manager
    with arena(capacity=256) as ar:
        b = ar.alloc(64)
        b[10] = 77
        assert b[10] == 77
    assert ar._is_closed


def test_tagged_template_literals():
    transpiler = RadicalTranspiler()
    source = """
def sql(query_str: str) -> str:
    return query_str.strip().upper()

let user_id = 99
let query = sql"SELECT * FROM users WHERE id = {user_id}"
"""
    py_code = transpiler.transpile(source)
    assert 'sql(f"SELECT * FROM users WHERE id = {user_id}")' in py_code
    locs = {}
    exec(py_code, locs)
    assert locs["query"] == "SELECT * FROM USERS WHERE ID = 99"


def test_compile_time_constant_folding():
    transpiler = RadicalTranspiler()
    source = """
const SECONDS = 24 * 60 * 60
const MEGABYTE = 1024 * 1024
const COMBO = (10 + 20) * 3
"""
    py_code = transpiler.transpile(source)
    # The constants must be folded into values
    assert "86400" in py_code or "SECONDS = 86400" in py_code
    assert "1048576" in py_code or "MEGABYTE = 1048576" in py_code
    assert "90" in py_code or "COMBO = 90" in py_code

    locs = {}
    exec(py_code, locs)
    assert locs["SECONDS"] == 86400
    assert locs["MEGABYTE"] == 1048576
    assert locs["COMBO"] == 90


def test_traits_protocol_transpilation():
    transpiler = RadicalTranspiler()
    source = """
trait Greeter:
    def greet(self) -> str:
        ...

class SpanishGreeter:
    def greet(self) -> str:
        return "Hola"

g = SpanishGreeter()
is_greeter = isinstance(g, Greeter)
"""
    py_code = transpiler.transpile(source)
    assert "class Greeter(typing.Protocol):" in py_code
    assert "@typing.runtime_checkable" in py_code
    locs = {}
    exec(py_code, locs)
    assert locs["is_greeter"] is True


def test_select_block_syntax():
    transpiler = RadicalTranspiler()
    source = """
let ch = chan[str](5)
ch.send("msg1")

let received = None
select:
    case val = ch.recv():
        received = val
    default:
        received = "default"
"""
    py_code = transpiler.transpile(source)
    assert "try_recv()" in py_code
    locs = {}
    exec(py_code, locs)
    assert locs["received"] == "msg1"


def test_buffer_hardening_f16_alignment_and_memoryview():
    # 1. f16 2-byte storage
    buf_f16 = buffer[f16](8)
    assert buf_f16.itemsize == 2
    assert buf_f16.nbytes == 16

    # 2. Alignment guarantee
    buf_aligned = buffer[f32](32, aligned=64)
    addr = ctypes.addressof(buf_aligned._raw_array)
    assert addr % 64 == 0

    # 3. Zero-copy memoryview
    buf = buffer[u8](16)
    buf[0] = 42
    mv = buf.to_memoryview()
    assert mv[0] == 42
    mv[0] = 99
    assert buf[0] == 99

    # 4. Typed pointer read/write inside unsafe
    with _rad_unsafe_context():
        ptr = buf.ptr
        ptr.write("u8", 1, 77)
        assert ptr.read("u8", 1) == 77


def test_nested_unsafe_depth_counter():
    from radical.runtime import _rad_unsafe_context, _rad_is_unsafe_active

    assert not _rad_is_unsafe_active()
    with _rad_unsafe_context():
        assert _rad_is_unsafe_active()
        with _rad_unsafe_context():
            assert _rad_is_unsafe_active()
        # Exiting inner context must still remain active in outer context!
        assert _rad_is_unsafe_active()
    assert not _rad_is_unsafe_active()


def test_native_fn_contract_validation():
    transpiler = RadicalTranspiler()

    # Supported primitive types succeed
    source_valid = """
native fn dot(a: float, b: float) -> float:
    return a * b
"""
    assert transpiler.transpile(source_valid) is not None

    # Unsupported dynamic types (like dict) must be rejected at compile time
    source_invalid_param = """
native fn process_dict(d: dict) -> int:
    return len(d)
"""
    with pytest.raises(RadicalCompileError) as exc_info:
        transpiler.transpile(source_invalid_param)
    assert "unsupported in native compiled tier" in str(exc_info.value)


def test_try_operator_return_type_contract():
    transpiler = RadicalTranspiler()

    # Using ? in function explicitly returning non-Result must fail
    source_invalid = """
fn bad_fn() -> int:
    val = Err("fail")?
    return 42
"""
    with pytest.raises(RadicalCompileError) as exc_info:
        transpiler.transpile(source_invalid)
    assert "must return Result or Option" in str(exc_info.value)


def test_cli_fmt_and_lint(tmp_path, capsys):
    src = tmp_path / "app.rad"
    src.write_text("let x = 10   \nlet y = 20\n", encoding="utf-8")

    # Test fmt
    ret_fmt = main(["fmt", "-w", str(src)])
    assert ret_fmt == 0
    assert src.read_text(encoding="utf-8") == "let x = 10\nlet y = 20\n"

    # Test lint on safe code
    ret_lint = main(["lint", str(src)])
    assert ret_lint == 0

    # Test lint on unsafe pointer leak
    bad_src = tmp_path / "bad.rad"
    bad_src.write_text("let p = buf.ptr\n", encoding="utf-8")
    ret_lint_bad = main(["lint", str(bad_src)])
    assert ret_lint_bad == 1


