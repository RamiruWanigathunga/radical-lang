"""
Diagnostics, invariant checking, and optimization explanations for Radical.
"""

import os
import sys
import argparse
from radical.transformer import RadicalTranspiler
from radical.exceptions import RadicalCompileError, RadicalSyntaxError


def print_error(err: Exception) -> None:
    """Formats and prints compiler and runtime errors with visual emphasis."""
    sys.stderr.write(f"\033[91mError:\033[0m {err}\n")


def cmd_check(args: argparse.Namespace) -> int:
    """Performs compile-time semantic and syntax validation without execution."""
    filepath = args.file
    if not os.path.exists(filepath):
        sys.stderr.write(f"\033[91mError:\033[0m File not found: '{filepath}'\n")
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        transpiler = RadicalTranspiler(filename=filepath)
        transpiler.transpile(source)

        print(f"\033[92mAll checks passed:\033[0m {filepath}")
        return 0

    except (RadicalCompileError, RadicalSyntaxError) as e:
        print_error(e)
        return 1


def cmd_explain(args: argparse.Namespace) -> int:
    """Explains compiler optimizations, lowerings, and execution targets for a Radical file."""
    filepath = args.file
    if not os.path.exists(filepath):
        sys.stderr.write(f"\033[91mError:\033[0m File not found: '{filepath}'\n")
        return 1

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        transpiler = RadicalTranspiler(filename=filepath)
        py_code = transpiler.transpile(source)

        print(f"\033[1;34mRadical Optimization & Execution Report:\033[0m {filepath}")
        print("=" * 70)
        if transpiler.last_explanations:
            for exp in transpiler.last_explanations:
                print(f"  \033[92m✔\033[0m {exp}")
        else:
            print("  \033[93m•\033[0m Standard Python execution path (no advanced lowering required)")

        print("-" * 70)
        if "simd" in py_code:
            print("  \033[36mSIMD:\033[0m 4-lane unrolled Python arithmetic fallback (CPU)")
        if "gpu" in py_code:
            from radical.gpu import gpu
            print(f"  \033[36mGPU:\033[0m  {gpu.device_name} (zero-copy memory worker dispatch)")
        if "_rad_parallel_for" in py_code:
            print("  \033[36mParallel:\033[0m Multi-core worker pool dispatch")
        if "_rad_native" in py_code:
            print("  \033[36mNative:\033[0m Fast numerical compiled tier (Numba JIT / fallback)")
        print("=" * 70)

        if getattr(args, "verbose", False):
            print("\n\033[1mEmitted Python Code Preview:\033[0m\n")
            print(py_code)

        return 0

    except (RadicalCompileError, RadicalSyntaxError) as e:
        print_error(e)
        return 1
