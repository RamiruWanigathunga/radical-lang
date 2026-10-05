"""
Radical Language Command-Line Interface (CLI).
Provides `radical run`, `radical build`, `radical check`, and interactive REPL.
"""

import os
import sys
import argparse
from typing import Optional
from radical import __version__
from radical.transformer import RadicalTranspiler
from radical.exceptions import RadicalCompileError, RadicalSyntaxError
from radical.cache import compute_content_hash, load_cached_code, save_cached_code
from radical.tools import (
    cmd_fmt,
    cmd_lint,
    cmd_check,
    cmd_explain,
    print_error,
)

# Export CLI functions for compatibility
__all__ = [
    "main",
    "create_parser",
    "cmd_run",
    "cmd_build",
    "cmd_check",
    "cmd_repl",
    "cmd_explain",
    "cmd_fmt",
    "cmd_lint",
    "print_error",
    "__version__",
]


def cmd_run(args: argparse.Namespace) -> int:
    """Executes a Radical (.rad) script directly in memory with zero disk writes."""
    filepath = args.file
    if not os.path.exists(filepath):
        sys.stderr.write(f"\033[91mError:\033[0m File not found: '{filepath}'\n")
        return 1

    try:
        abs_path = os.path.abspath(filepath)
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        content_hash = compute_content_hash(source, __version__)
        compiled = load_cached_code(abs_path, content_hash, __version__)

        if compiled is None:
            transpiler = RadicalTranspiler(filename=filepath)
            tree, py_code = transpiler.transpile_ast(source)
            compiled = compile(tree if tree is not None else py_code, filepath, "exec")
            save_cached_code(abs_path, content_hash, __version__, compiled)

        # Adjust sys.argv for the executed script
        orig_argv = sys.argv
        sys.argv = [filepath] + (args.script_args or [])

        main_mod = sys.modules.get("__main__")
        orig_file = getattr(main_mod, "__file__", None)
        orig_doc = getattr(main_mod, "__doc__", None)

        if main_mod is not None:
            main_mod.__file__ = abs_path
            main_mod.__doc__ = None
            global_namespace = main_mod.__dict__
        else:
            global_namespace = {
                "__name__": "__main__",
                "__file__": abs_path,
                "__doc__": None,
            }

        try:
            exec(compiled, global_namespace)
        finally:
            sys.argv = orig_argv
            if main_mod is not None:
                if orig_file is not None:
                    main_mod.__file__ = orig_file
                if orig_doc is not None:
                    main_mod.__doc__ = orig_doc

        return 0

    except (RadicalCompileError, RadicalSyntaxError) as e:
        print_error(e)
        return 1
    except Exception:
        import traceback
        traceback.print_exc()
        return 1


def cmd_build(args: argparse.Namespace) -> int:
    """Transpiles a Radical (.rad) script into standard Python 3.10+ code."""
    filepath = args.file
    if not os.path.exists(filepath):
        sys.stderr.write(f"\033[91mError:\033[0m File not found: '{filepath}'\n")
        return 1

    outpath = args.output
    if not outpath:
        if filepath.endswith(".rad"):
            outpath = filepath[:-4] + ".py"
        else:
            outpath = filepath + ".py"

    try:
        with open(filepath, "r", encoding="utf-8") as f:
            source = f.read()

        transpiler = RadicalTranspiler(filename=filepath)
        py_code = transpiler.transpile(source)

        with open(outpath, "w", encoding="utf-8") as f:
            f.write(py_code)

        print(f"\033[92mSuccess:\033[0m Transpiled {filepath} -> {outpath}")
        return 0

    except (RadicalCompileError, RadicalSyntaxError) as e:
        print_error(e)
        return 1


def cmd_repl() -> int:
    """Starts the interactive Radical REPL."""
    print(f"Radical {__version__} Interactive Shell")
    print("Type 'exit()' or Ctrl-D to exit.")

    transpiler = RadicalTranspiler(filename="<repl>")
    repl_namespace = {
        "__name__": "__main__",
        "__doc__": None,
    }

    while True:
        try:
            line = input("rad> ")
            if line.strip() in ("exit", "exit()", "quit", "quit()"):
                break
            if not line.strip():
                continue

            # If user enters an expression, transpile and evaluate
            py_code = transpiler.transpile(line)
            try:
                # Try evaluating as expression first
                res = eval(py_code, repl_namespace)
                if res is not None:
                    print(repr(res))
            except SyntaxError:
                # Otherwise execute as statement
                exec(py_code, repl_namespace)

        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break
        except (RadicalCompileError, RadicalSyntaxError) as e:
            print_error(e)
        except Exception as e:
            print(f"\033[91mRuntime Error:\033[0m {e}")

    return 0


def create_parser() -> argparse.ArgumentParser:
    """Creates the Radical argument parser."""
    parser = argparse.ArgumentParser(
        prog="radical",
        description="Radical (.rad): High-productivity, performance-oriented superset of Python with Mojo-style SIMD/Metal GPU acceleration.",
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"Radical {__version__} (Python superset with Mojo-style SIMD/Metal acceleration)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # `radical run <file.rad>`
    run_parser = subparsers.add_parser("run", help="Execute a Radical script in memory")
    run_parser.add_argument("file", help="Path to .rad source file")
    run_parser.add_argument("script_args", nargs="*", help="Arguments passed to script")

    # `radical build <file.rad> [-o out.py]`
    build_parser = subparsers.add_parser("build", help="Transpile a Radical script to Python")
    build_parser.add_argument("file", help="Path to .rad source file")
    build_parser.add_argument("-o", "--output", help="Output file path (defaults to <file>.py)")

    # `radical check <file.rad>`
    check_parser = subparsers.add_parser("check", help="Verify syntax and compile-time const invariants")
    check_parser.add_argument("file", help="Path to .rad source file")

    # `radical explain <file.rad>`
    explain_parser = subparsers.add_parser("explain", help="Display compiler optimizations, lowerings, and execution targets")
    explain_parser.add_argument("file", help="Path to .rad source file")
    explain_parser.add_argument("-v", "--verbose", action="store_true", help="Print emitted Python preview")

    # `radical repl`
    subparsers.add_parser("repl", help="Start the interactive Radical REPL")

    # `radical fmt <file.rad> [-w]`
    fmt_parser = subparsers.add_parser("fmt", help="Format Radical source files with canonical style")
    fmt_parser.add_argument("file", help="Path to .rad source file")
    fmt_parser.add_argument("-w", "--write", action="store_true", help="Write formatted code back to source file")

    # `radical lint <file.rad>`
    lint_parser = subparsers.add_parser("lint", help="Lint Radical source files for unsafe pointer escapes and safety invariants")
    lint_parser.add_argument("file", help="Path to .rad source file")

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    """Main entry point for Radical CLI."""
    parser = create_parser()

    if argv is None:
        argv = sys.argv[1:]

    # If no arguments provided, enter REPL
    if not argv:
        return cmd_repl()

    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    elif args.command == "build":
        return cmd_build(args)
    elif args.command == "check":
        return cmd_check(args)
    elif args.command == "repl":
        return cmd_repl()
    elif args.command == "explain":
        return cmd_explain(args)
    elif args.command == "fmt":
        return cmd_fmt(args)
    elif args.command == "lint":
        return cmd_lint(args)
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    sys.exit(main())
