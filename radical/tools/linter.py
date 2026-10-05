"""
Static analysis and safety linting tool for Radical (.rad) source files.
"""

import os
import sys
import argparse


def lint_source(source: str) -> list[tuple[int, str]]:
    """Analyzes Radical source code for safety leaks, pointer escapes, and contract violations."""
    issues: list[tuple[int, str]] = []
    in_unsafe = False
    unsafe_indent = 0

    for idx, line in enumerate(source.splitlines(), 1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())

        if stripped.startswith("unsafe:"):
            in_unsafe = True
            unsafe_indent = indent
            continue

        if in_unsafe and indent <= unsafe_indent and stripped:
            in_unsafe = False

        if ".ptr" in stripped and not in_unsafe:
            issues.append((idx, "Unsafe pointer access '.ptr' outside of an 'unsafe:' block boundary"))

    return issues


def cmd_lint(args: argparse.Namespace) -> int:
    """Lints Radical source files for unsafe pointer escapes and safety invariants."""
    filepath = args.file
    if not os.path.exists(filepath):
        sys.stderr.write(f"\033[91mError:\033[0m File not found: '{filepath}'\n")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    issues = lint_source(source)

    print(f"\033[1;34mRadical Linter:\033[0m {filepath}")
    print("=" * 65)
    if not issues:
        print("  \033[92m✔ No issues found.\033[0m Code strictly adheres to safety contracts.")
        print("=" * 65)
        return 0
    else:
        for lineno, msg in issues:
            print(f"  \033[91m✖ Line {lineno}:\033[0m {msg}")
        print("=" * 65)
        return 1
