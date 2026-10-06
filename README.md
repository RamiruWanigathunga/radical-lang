# Radical (`.rad`)

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-Apache%202.0-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-114%20passing-brightgreen)](tests/)
[![GPU](https://img.shields.io/badge/GPU-Zero--CUDA%20Apple%20Metal-orange)](radical/gpu/)

> **A productivity-first, performance-oriented strict superset of Python 3.10+.**

Radical brings modern programming ergonomics, compile-time immutability, systems-grade memory primitives, and Mojo-style SIMD/Apple Silicon Metal GPU acceleration directly to Python.

$$S_{\text{Python 3.10+}} \subset S_{\text{Radical}}$$

Every valid Python 3.10+ program is a 100% valid Radical program. Radical runs alongside existing PyPI packages (`numpy`, `torch`, `pandas`, `fastapi`), compiles directly to standard Python 3.10+ AST and bytecode, and introduces zero vendor or runtime lock-in.

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
  - [Command-Line Interface (CLI)](#command-line-interface-cli)
  - [Programmatic Python API](#programmatic-python-api)
  - [Code Comparison](#code-comparison)
- [Examples](#examples)
- [Benchmarks](#benchmarks)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

---

## Features

Radical introduces targeted, high-impact features designed to eliminate defensive boilerplate while unlocking systems-level hardware performance:

| Feature | Radical Syntax | How It Lowers | Primary Benefit |
| :--- | :--- | :--- | :--- |
| **Pipeline Operator** | `val \|> f(_) \|> g(_)` | Fuses into list comprehensions or nested calls | Eliminates inverted call nesting; creates natural left-to-right data flow |
| **Arrow Functions** | `(x) => x * 2` | `lambda x: x * 2` (or inlined in comprehensions) | Concise single-expression lambdas |
| **Safe Navigation** | `obj?.attr`, `arr?[idx]` | Safe runtime accessors returning `None` | Eliminates defensive `if obj is not None:` and `IndexError` / `KeyError` crashes |
| **Nullish Coalescing** | `a ?? fallback`, `a ??=` | Null-strict ternary `a if a is not None else fallback` | Preserves valid falsy values (`0`, `False`, `""`); avoids Python `or` pitfalls |
| **Range Literals** | `0..N`, `1..=N`, `0..N..step` | `range(0, N)`, `range(1, N + 1)` | Intuitive half-open and inclusive numeric sequences |
| **Cartesian Loops** | `for x, y in (A x B):` | C-accelerated `itertools.product(A, B)` | Multi-dimensional matrix loops without nested indentation bloat |
| **Immutability Invariants** | `const NAME = val` | Tracked compile-time constant symbol | Catches accidental variable reassignments before code executes |
| **Mutable Bindings** | `let name = val` | Standard assignment `name = val` | Explicitly declares state accumulators |
| **Slotted Structs** | `struct Point(x: float, y: float)` | `@dataclass(slots=True, frozen=True)` | Immutable records with 3x memory reduction and O(1) attribute access |
| **Functional Copy-With** | `p with { x: 10 }` | `dataclasses.replace(p, x=10)` | Non-destructive functional record updates |
| **Algebraic Data Types** | `enum Shape: Circle(...) Rect(...)` | Sealed class hierarchy of frozen dataclasses | Tagged union variants supporting Python `match / case` |
| **Error Propagation** | `val?` (with `Result[T, E]`) | Inlined `if res.is_err(): return res` | Rust-style zero-cost error propagation; 5x faster than exceptions |
| **Deterministic Cleanup** | `defer expr` | `_RadicalDeferStack` in LIFO order | Guaranteed LIFO resource management upon function exit or error |
| **Hardware SIMD Math** | `simd[float, 4](...)` | Unrolled 4-lane hardware vector registers | Single-instruction multiple-data arithmetic with `.dot()` and `.sum()` |
| **Contiguous Memory Buffers**| `buffer[f32](size)` | Unboxed cache-line aligned ctypes memory | Zero-copy slicing with scoped `unsafe:` pointer math |
| **Multi-Core Parallelism** | `parallel for i in 0..N:` | Multiprocessing worker pools | Multi-core CPU scheduling bypassing Python's GIL |
| **Apple Metal GPU Loops** | `gpu for i in 0..N:` | Apple Metal compute shaders | Zero-CUDA GPU compute on Apple Silicon Unified Memory |
| **Native Fastmath JIT** | `native fn calc(...):` | `@_rad_native` (Numba JIT fastmath) | LLVM machine code execution for numerical loops |

---

## Prerequisites

- **Python**: `>= 3.10` (Tested on 3.10, 3.11, 3.12)
- **Operating System**: Linux, macOS, or Windows
- **Optional Accelerators**:
  - **Apple Silicon GPU**: macOS 12+ on M-series chips (`pyobjc-framework-Metal`)
  - **Fastmath JIT**: `numba>=0.58.0` for `native fn` machine compilation

---

## Installation

### From Source (Development)
```bash
# Clone the repository
git clone https://github.com/RamiruWanigathunga/radical-lang.git
cd radical-lang

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in editable mode with development dependencies
pip install -e ".[dev]"
```

### Optional Feature Packages
```bash
# Install with Apple Metal GPU support (macOS only)
pip install -e ".[metal]"

# Install with Numba JIT fastmath support
pip install -e ".[native]"
```

---

## Configuration

Radical is designed to run with zero configuration out of the box. Optional environment variables include:

| Environment Variable | Default | Purpose |
| :--- | :--- | :--- |
| `RADICAL_CACHE_DIR` | `__radcache__` | Directory for storing compiled `.pyc` bytecode cache files |
| `RADICAL_DISABLE_CACHE` | `0` | Set to `1` to bypass bytecode caching during development |
| `RADICAL_WORKERS` | CPU count | Default worker process count for `parallel for` loops |

---

## Usage

### Command-Line Interface (CLI)

Radical includes a complete developer toolchain:

```bash
# 1. Execute a .rad file directly in memory (with SHA-256 bytecode caching)
radical run script.rad

# 2. Transpile .rad source to standard Python 3.10+ AST
radical build script.rad -o dist/bundle.py

# 3. Verify syntax and compile-time const invariants without running
radical check script.rad

# 4. Inspect compiler optimizations (pipeline fusion, constant folding, GPU targets)
radical explain script.rad -v

# 5. Format Radical source code with canonical style
radical fmt -w script.rad

# 6. Lint code for unsafe pointer escapes and safety invariants
radical lint script.rad

# 7. Start the interactive REPL
radical repl
```

### Programmatic Python API

You can use the Radical compiler directly inside standard Python applications:

```python
from radical.transformer import RadicalTranspiler

# Initialize transpiler
transpiler = RadicalTranspiler(filename="pipeline.rad")

# Transpile Radical source code to Python
source_rad = """
const numbers = [1, 2, 3, 4, 5]
const squares = numbers |> filter((x) => x % 2 != 0, _) |> map((x) => x * x, _) |> list
"""

python_code = transpiler.transpile(source_rad)
print(python_code)
```

### Code Comparison

#### 1. Pipeline Processing & Safe Navigation

**Radical (`.rad`)**
```radical
const raw_users = [
    {"name": "Alice", "score": 95, "tags": ["admin", "dev"]},
    {"name": "Bob", "score": 0, "tags": None},
]

# Pipeline & safe navigation
const top_performers = raw_users
    |> filter((u) => (u?.score ?? 0) > 50, _)
    |> map((u) => u?.name?.upper(), _)
    |> list

print("Top Performers:", top_performers)
```

**Equivalent Standard Python**
```python
raw_users = [
    {"name": "Alice", "score": 95, "tags": ["admin", "dev"]},
    {"name": "Bob", "score": 0, "tags": None},
]

# Defensive list comprehension
top_performers = [
    u["name"].upper()
    for u in raw_users
    if (u.get("score") if u.get("score") is not None else 0) > 50
    and u.get("name") is not None
]

print("Top Performers:", top_performers)
```

#### 2. Multi-Dimensional Iteration (Cartesian Loops)

**Radical (`.rad`)**
```radical
const WIDTH = 4
const HEIGHT = 3

# Cartesian product replaces nested loops
let grid = []
for row, col in (0..HEIGHT x 0..WIDTH):
    grid.append((row, col))

print("Grid points:", len(grid))
```

**Equivalent Standard Python**
```python
WIDTH = 4
HEIGHT = 3

# Nested loops
grid = []
for row in range(HEIGHT):
    for col in range(WIDTH):
        grid.append((row, col))

print("Grid points:", len(grid))
```

---

## Examples

Radical includes **16 verified, runnable code examples** categorized across three difficulty tiers:

| Tier | Directory | Key Examples |
| :--- | :--- | :--- |
| **Beginner** | [`examples/01_beginner/`](examples/01_beginner/) | Pipelines (`01`), Safe Nav & Coalescing (`02`), Range Literals (`03`), `let`/`const` (`04`), Destructuring (`05`) |
| **Intermediate** | [`examples/02_intermediate/`](examples/02_intermediate/) | Slotted Structs & Copy-With (`01`), ADT Enums (`02`), Result Error Handling (`03`), Defer & Using (`04`), Cartesian Loops (`05`) |
| **Advanced** | [`examples/03_advanced/`](examples/03_advanced/) | Multi-Core Parallelism (`01`), Hardware SIMD (`02`), Raw Memory & Unsafe (`03`), Channels & Select (`04`), Zero-CUDA Metal GPU (`05`), Native Fastmath (`06`) |

Run all examples in sequence:
```bash
for f in examples/*/*.rad; do radical run "$f"; done
```

For full descriptions of all examples, see [`examples/README.md`](examples/README.md).

---

## Benchmarks

Radical programs compiled ahead-of-time with `radical build` execute at pure hardware speed with zero transpilation overhead. On massive, compute-heavy workloads, Radical consistently outperforms standard single-threaded Python across multi-core CPU scheduling, hardware SIMD, memory buffers, and Apple Silicon Metal GPU acceleration:

| Benchmark Category | Workload Scale | Standard Python | Radical (Pre-Built) | Speedup | Winner |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **GPU Acceleration** (Apple Metal) | 450M Elements | 33.21s | 3.84s | **8.65x** | **Radical** |
| **Memory Architecture** (Raw Buffer) | 600M Writes | 47.05s | 6.92s | **6.80x** | **Radical** |
| **Iteration & Loops** (Cartesian Grid) | 400M Coordinates | 37.03s | 5.70s | **6.50x** | **Radical** |
| **Parallelism & Numerics** (Multi-Core Prime) | 16M Range | 55.45s | 9.09s | **6.10x** | **Radical** |
| **Fractal Computation** (Mandelbrot) | 2500x2500 Grid | 40.91s | 6.70s | **6.11x** | **Radical** |
| **Safe Coalescing** (Nullish Check) | 1.2B Resolves | 29.55s | 5.08s | **5.82x** | **Radical** |
| **Destructuring Extraction** | 400M Extractions | 29.34s | 7.98s | **3.68x** | **Radical** |
| **Parallel Linear Algebra** (Matrix Mult) | 900x900 Matrix | 1m 41.7s | 43.84s | **2.32x** | **Radical** |
| **Hardware SIMD** (Vector Dot Product) | 350M Ops | 22.45s | 9.38s | **2.39x** | **Radical** |

> **Cumulative Suite Result**: Radical completed the entire 12-benchmark suite in **2m 15s** vs Python's **8m 24s** (**3.73x overall suite speedup**, winning 12 of 12 benchmarks).  
> For full methodology and detailed benchmark breakdowns, see [`benchmarks/BENCHMARK_RESULTS.md`](benchmarks/BENCHMARK_RESULTS.md).

Run the entire benchmark suite:
```bash
python benchmarks/run_all.py
```

---

## Development

```bash
# Clone and enter repo
git clone https://github.com/RamiruWanigathunga/radical-lang.git
cd radical-lang

# Install dev dependencies
pip install -e ".[dev]"

# Format code
radical fmt -w file.rad

# Lint code
radical lint file.rad
```

---

## Testing

Radical maintains 100% passing test coverage across all features:

```bash
# Run full pytest suite (114 passing tests in ~0.3s)
pytest

# Run tests with verbose output
pytest -v

# Run specific subsystem test
pytest tests/test_pipeline.py
pytest tests/test_v2_features.py
```

---

## Deployment

Because Radical compiles to standard Python 3.10+ AST and bytecode, deployment requires zero custom runtime infrastructure:

```bash
# Ahead-of-time (AOT) transpile all .rad files to .py
radical build app.rad -o dist/app.py

# Run directly in standard Python in production containers:
python dist/app.py
```

---

## Troubleshooting

### 1. `RadicalCompileError: Cannot reassign constant 'X'`
- **Cause**: A variable declared with `const X = ...` was reassigned or mutated with `+=` / `-=`.
- **Solution**: If the variable represents an accumulator or changing state, declare it with `let x = ...` instead.

### 2. `Syntax error in emitted code` during pipeline chaining
- **Cause**: Multiline pipelines missing line continuation indentation.
- **Solution**: Ensure each pipeline step begins with `|> ` and uses the `_` placeholder if passing into non-first arguments (e.g. `items |> filter(fn, _)`).

### 3. Apple Metal GPU fallback on Linux / Windows
- **Notice**: `gpu for` automatically detects Apple Silicon hardware. On non-macOS systems or systems without Metal drivers, it executes safely using CPU vector fallback without raising errors.

---

## Contributing

We welcome contributions from the community! Please read our [Contributing Guidelines](CONTRIBUTING.md) and [Code of Conduct](CODE_OF_CONDUCT.md) before opening a pull request.

- **Found a bug?** Open an issue with our [Bug Report Template](.github/ISSUE_TEMPLATE/bug_report.md).
- **Proposing syntax?** Submit an enhancement using our [Feature Request Template](.github/ISSUE_TEMPLATE/feature_request.md).

---

## License

Radical is open-source software licensed under the **[Apache License 2.0](LICENSE)**.
Copyright 2026 The Radical Language Authors.
