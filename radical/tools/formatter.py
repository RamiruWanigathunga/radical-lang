"""
Code formatting tool for Radical source files (.rad).
"""

import os
import sys
import argparse


def format_source(source: str) -> str:
    """Formats Radical source text with canonical whitespace and line endings."""
    lines = source.splitlines(keepends=True)
    formatted_lines = [line.rstrip() + "\n" if line.strip() else "\n" for line in lines]
    return "".join(formatted_lines).rstrip() + "\n"


def cmd_fmt(args: argparse.Namespace) -> int:
    """Formats a Radical source file with canonical indentation and spacing."""
    filepath = args.file
    if not os.path.exists(filepath):
        sys.stderr.write(f"\033[91mError:\033[0m File not found: '{filepath}'\n")
        return 1

    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()

    formatted_code = format_source(source)

    if getattr(args, "write", False):
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(formatted_code)
        print(f"\033[92m✔\033[0m Formatted {filepath}")
    else:
        sys.stdout.write(formatted_code)
    return 0
