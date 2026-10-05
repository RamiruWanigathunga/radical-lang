"""
End-to-end integration tests running .rad files through the CLI.
"""

from pathlib import Path
from radical.cli import main


def test_e2e_radical_suite(capsys):
    test_file = Path(__file__).parent / "test_radical.rad"
    exit_code = main(["run", str(test_file)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "All Core Radical Features Verified Successfully!" in captured.out


def test_e2e_mojo_suite(capsys):
    test_file = Path(__file__).parent / "test_mojo_features.rad"
    exit_code = main(["run", str(test_file)])
    assert exit_code == 0
    captured = capsys.readouterr()
    assert "All Mojo-Style Systems Features Verified Successfully!" in captured.out
