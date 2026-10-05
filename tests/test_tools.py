"""
Unit tests for developer tools and cache subsystem.
"""

from radical.tools.formatter import format_source
from radical.tools.linter import lint_source
from radical.cache import compute_content_hash, load_cached_code, save_cached_code, get_cache_path


def test_format_source_whitespace_cleanup():
    unformatted = "const x = 10   \nlet y = 20\t\n\n\n"
    formatted = format_source(unformatted)
    assert formatted == "const x = 10\nlet y = 20\n"


def test_linter_detects_unsafe_ptr():
    safe_code = """
unsafe:
    let ptr = buf.ptr
    let val = ptr.read[f32](0)
"""
    issues = lint_source(safe_code)
    assert len(issues) == 0

    unsafe_leak = """
let ptr = buf.ptr
"""
    issues_bad = lint_source(unsafe_leak)
    assert len(issues_bad) == 1
    assert "outside of an 'unsafe:' block boundary" in issues_bad[0][1]


def test_cache_compute_and_save_load(tmp_path):
    src_file = tmp_path / "sample.rad"
    src_file.write_text("const answer = 42\n", encoding="utf-8")
    version = "0.1.0"
    content = src_file.read_text(encoding="utf-8")
    content_hash = compute_content_hash(content, version)

    compiled_obj = compile("answer = 42", str(src_file), "exec")
    save_cached_code(str(src_file), content_hash, version, compiled_obj)

    loaded = load_cached_code(str(src_file), content_hash, version)
    assert loaded is not None

    ns = {}
    exec(loaded, ns)
    assert ns["answer"] == 42
