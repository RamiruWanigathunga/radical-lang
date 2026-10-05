# Radical Command-Line Interface (CLI) Guide

The `radical` command-line utility provides comprehensive tools for running, building, testing, linting, formatting, and analyzing Radical (`.rad`) code.

---

## 1. Quick Command Summary

| Command | Usage | Description |
| :--- | :--- | :--- |
| **`run`** | `radical run <script.rad> [args...]` | In-memory JIT execution with SHA-256 bytecode caching. |
| **`build`** | `radical build <script.rad> [-o out.py]` | Transpiles `.rad` source code into production Python 3.10+ AST. |
| **`check`** | `radical check <script.rad>` | Validates syntax and verifies compile-time immutability invariants. |
| **`explain`** | `radical explain <script.rad> [-v]` | Details compiler optimizations (pipeline fusion, constant folding, SIMD/GPU lowering). |
| **`repl`** | `radical repl` | Launches the interactive Radical shell. |
| **`fmt`** | `radical fmt <script.rad> [-w]` | Formats Radical source files with canonical style. |
| **`lint`** | `radical lint <script.rad>` | Lints source files for unsafe pointer escapes and safety invariants. |

---

## 2. Command Details

### 2.1 `radical run`
Executes a Radical script directly in memory:
```bash
# Basic execution
radical run examples/01_beginner/01_pipeline_data_flow.rad

# Passing arguments to the executed script
radical run server.rad --port 8080 --host 0.0.0.0
```
- **Bytecode Caching**: Radical caches compiled bytecode in adjacent `__radcache__/*.pyc` files using SHA-256 source hashing, achieving sub-millisecond start times on subsequent invocations.

### 2.2 `radical build`
Transpiles Radical into standalone Python 3.10+ files for production deployment:
```bash
# Transpile script.rad -> script.py
radical build script.rad

# Specify custom output path
radical build script.rad -o dist/bundle.py
```

### 2.3 `radical check`
Performs static analysis without executing code:
```bash
radical check script.rad
```
- Verifies lexical syntax.
- Validates that `const` symbols are never reassigned.
- Checks parameter type annotations on strict functions.

### 2.4 `radical explain`
Inspects compiler passes and lowering decisions:
```bash
radical explain examples/01_beginner/01_pipeline_data_flow.rad
```
Output:
```text
Radical Optimization & Execution Report: examples/01_beginner/01_pipeline_data_flow.rad
======================================================================
  ✔ line 14: pipeline fused → Python list comprehension
  ✔ line 17: pipeline step → direct function call
----------------------------------------------------------------------
======================================================================
```
Use `-v` / `--verbose` to view the emitted Python code alongside optimizations.

### 2.5 `radical fmt`
Formats code according to standard Radical guidelines:
```bash
# Preview formatted changes
radical fmt script.rad

# Write changes back to the source file
radical fmt -w script.rad
```

### 2.6 `radical lint`
Detects safety violations, unmanaged pointers, and unsafe block escapes:
```bash
radical lint script.rad
```

### 2.7 `radical repl`
Launches the interactive Read-Eval-Print Loop:
```bash
radical repl
rad> const nums = [1, 2, 3] |> map((x) => x * 10, _) |> list
rad> nums
[10, 20, 30]
rad> exit()
```
