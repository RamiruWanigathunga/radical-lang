"""
Tests for Radical CLI (radical run, build, check, --version).
"""

import sys
import tempfile
from pathlib import Path
import pytest
from radical.cli import main


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])
    assert exc_info.value.code == 0
    captured = capsys.readouterr()
    assert "Radical 0.1.0" in captured.out or "Radical 0.1.0" in captured.err


def test_cli_run_valid_script(tmp_path, capsys):
    script = tmp_path / "hello.rad"
    script.write_text('const msg = "Radical Works!"\nprint(msg)\n', encoding="utf-8")

    code = main(["run", str(script)])
    assert code == 0
    captured = capsys.readouterr()
    assert "Radical Works!" in captured.out


def test_cli_run_with_argv(tmp_path, capsys):
    script = tmp_path / "args.rad"
    script.write_text('import sys\nprint(f"ARGS:{sys.argv[1]}")\n', encoding="utf-8")

    code = main(["run", str(script), "custom_argument"])
    assert code == 0
    captured = capsys.readouterr()
    assert "ARGS:custom_argument" in captured.out


def test_cli_build(tmp_path):
    src = tmp_path / "test.rad"
    out = tmp_path / "out.py"
    src.write_text('const x = 42 |> (val) => val * 2\n', encoding="utf-8")

    code = main(["build", str(src), "-o", str(out)])
    assert code == 0
    assert out.exists()
    content = out.read_text(encoding="utf-8")
    assert "x =" in content
    assert "lambda" in content


def test_cli_check_success(tmp_path, capsys):
    src = tmp_path / "check_ok.rad"
    src.write_text('const VALID = 100\n', encoding="utf-8")

    code = main(["check", str(src)])
    assert code == 0
    captured = capsys.readouterr()
    assert "All checks passed" in captured.out


def test_cli_check_failure(tmp_path, capsys):
    src = tmp_path / "check_fail.rad"
    src.write_text('const X = 10\nX = 20\n', encoding="utf-8")

    code = main(["check", str(src)])
    assert code == 1
    captured = capsys.readouterr()
    assert "Error:" in captured.err
    assert "Cannot reassign constant" in captured.err


def test_cli_file_not_found(capsys):
    code = main(["run", "nonexistent_file_xyz.rad"])
    assert code == 1
    captured = capsys.readouterr()
    assert "File not found" in captured.err
