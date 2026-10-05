# Radical (.rad) Complete Learning Guide for Python Developers

Welcome to the official Radical curriculum! This guide is specifically written for Python programmers who want to master Radical from ground zero to high-performance systems engineering.

---

## Learning Roadmap

```
├── 01_beginner/
│   ├── 01_python_to_radical.md        # The 100% Superset Rule & CLI Tools
│   ├── 02_pipes_and_arrows.md         # |> Pipelines & => Arrow Functions
│   └── 03_safe_navigation.md          # ?. Safe Navigation & ?? Nullish Coalescing
│
├── 02_intermediate/
│   ├── 01_ranges_and_loops.md         # 0..10 Ranges & (A x B) Cartesian Loops
│   ├── 02_const_and_defer.md          # const Invariance & defer Resource Cleanup
│   └── 03_structs_and_destructuring.md# Slotted struct Types & Dict Unpacking
│
├── 03_advanced/
│   ├── 01_parallel_computing.md       # Multi-Core parallel for (Bypassing the GIL)
│   ├── 02_simd_and_raw_memory.md      # SIMD Vectors & Continuous raw Buffers
│   └── 03_zero_cuda_gpu.md            # Apple Silicon Metal GPU Acceleration
│
└── 04_performance_guide.md            # The Definitive Performance Dossier
```

---

## Quick Reference: Python vs Radical

| Feature | Standard Python | Radical (.rad) | Benefit |
|---|---|---|---|
| **Superset** | Valid Python 3.10+ | Same code runs unmodified | 100% interoperability |
| **Pipelines & Fusion** | `list(map(f, filter(p, data)))` | `data \|> filter(p) \|> map(f) \|> list` | Fuses into comprehension (**2.79x faster**) |
| **Anonymous Fn** | `lambda x, y: x + y` | `(x, y) => x + y` | Clean, modern arrow syntax |
| **Safe Navigation** | `user.profile.name if user and user.profile else None` | `user?.profile?.name` | Stops `NoneType` crashes |
| **Nullish Default** | `x if x is not None else default` | `x ?? default` | Keeps `0`, `False`, `""` |
| **Error Propagation** | `if res.is_err: return res` | `val = fetch()?` | Rust-style `?` operator |
| **Ranges** | `range(0, 10)` and `range(1, 11)` | `0..10` and `1..=10` | Mathematical interval notation |
| **Cartesian Loop** | Nested `for x in ...:` inside `for y in ...:` | `for x, y in (0..w x 0..h):` | Flat 1-line multi-loops |
| **Immutability** | None (convention only) | `const API_KEY = "xyz"` | Compile-time reassignment check |
| **Explicit Mutable** | `count = 0` | `let count = 0` | Explicit mutable declaration |
| **Resource Cleanup**| Nested `with open(...) as f:` blocks | `using f = open(...):` / `defer` | Scoped block / LIFO cleanup |
| **Value Types** | `@dataclass(slots=True, frozen=True)` | `struct Point(x: float, y: float)` | Memory-lean value objects |
| **Struct Update** | `dataclasses.replace(p, x=10)` | `p with { x: 10 }` | Functional copy-update |
| **Traits & Protocols** | `@typing.runtime_checkable class P(Protocol):` | `trait Printable: def to_string(...)` | Structural typing with `isinstance` |
| **Enums & ADTs** | Verbose class hierarchies | `enum Shape: Circle(r), Rect(w, h)` | Pattern-matchable algebraic types |
| **Typed Buffers** | `ctypes` or `bytearray` | `buffer[f32](1024, aligned=64)` | Hardware-aligned zero-copy slices |
| **Memory Arena** | Manual buffer reuse | `using a = arena(size):` | Bulk $O(1)$ scoped deallocation |
| **Scoped Unsafe** | Unchecked operations everywhere | `unsafe: ptr.write[f32](i, v)` | Explicit unsafe boundary with depth counter |
| **Channels** | Complex `queue.Queue` setup | `chan[str](10)` & `select:` | Go-style typed concurrency |
| **Native Fast Tier** | Manual Numba `@jit` | `native fn dot(...) -> f32:` | Restricted compiled machine code |
| **Multi-Core Loops** | 20 lines of `multiprocessing.Pool` | `parallel for i in 0..N:` | **5x faster** on multi-core CPUs |
| **Parallel Comp** | Complex `pool.map(...)` | `parallel [f(x) for x in items]` | Built-in multi-core list comprehensions |

---

## Quick Start: Running & Building

```bash
# 1. Run directly in memory (zero disk footprint, bytecode cached)
radical run script.rad

# 2. Explain compiler optimizations and backend diagnostics
radical explain script.rad
radical explain script.rad -v

# 3. Canonical code formatter
radical fmt script.rad -w

# 4. Static safety linter (detect pointer escapes and type contract violations)
radical lint script.rad

# 5. Transpile to clean standard Python 3.10+
radical build script.rad -o script.py

# 6. Check for compile errors and const violations without running
radical check script.rad

# 7. Interactive REPL shell
radical repl
```

