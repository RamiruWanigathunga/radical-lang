# The Definitive Performance Dossier

## 1. Executive Summary
Because Radical compiles directly to standard Python 3.10+ AST and bytecode, its performance falls into three transparent categories:

```
                            RADICAL PERFORMANCE PROFILE
   Micro-Safety (~9ns)              Equal (1.0x Parity)             Much Faster (2.8x - 5.5x)
 ◄──────────────────────────────┼─────────────────────────┼────────────────────────►
   Safe Navigation (`?.`)          Arrow funcs (`=>`)        Multi-core (`parallel for`, `parallel [...]`)
   (Guarantees crash-free code)    Destructuring (`{ a }`)   Pipeline Fusion (`\|> filter \|> map \|> list`)
                                   Standard Python code      SIMD 4-Lane Unrolling (`simd4`)
                                   Cartesian loops (`A x B`) Slotted Structs (`struct`)
                                   Nullish Coalescing (`??`) Bytecode Cache (`__radcache__`)
```

---

## 2. Heavy Compute Workloads: Radical WINS by 5x

On compute-intensive tasks, standard Python is limited to a single CPU core by the CPython GIL. Radical's `parallel(mode="process")` and `parallel [...]` bypass the GIL and engage all CPU cores with Unix Copy-on-Write memory sharing:

| Benchmark | Workload | Standard Python | Radical (.rad) | Speedup | Winner |
|---|---|:---:|:---:|:---:|:---:|
| **3D Multi-Sphere Ray Tracer** | 360,000 primary rays, 7 spheres, lighting | `1.417 s` | `0.316 s` | **4.49x** | **Radical** |
| **Mandelbrot Fractal Engine** | 800x800 complex plane, 192M ops | `2.758 s` | `0.527 s` | **5.24x** | **Radical** |
| **Monte Carlo Asset Pricing** | 8,000,000 stochastic paths, Box-Muller | `2.591 s` | `0.505 s` | **5.13x** | **Radical** |
| **2D 5x5 Image Convolution** | 2000x2000 image matrix, 100M MAC ops | `4.083 s` | `0.856 s` | **4.77x** | **Radical** |
| **TOTAL RUNTIME** | 4 Combined Compute Programs | **`10.849 s`** | **`2.203 s`** | **4.92x** | **Radical** |

> *Reproduce locally: `.venv/bin/python benchmarks/showdown/run_showdown.py`*

---

## 3. Micro & Ergonomic Operations: Up to 3.5x Faster

For everyday syntax transformations and data processing:

- **Pipeline Fusion (`data |> filter(...) |> map(...) |> list`)**: **2.79x faster** (0.1764s vs 0.4922s for 100k items) because it eliminates intermediate iterator objects and inlines arrow closures directly into list comprehensions.
- **SIMD 4-Lane Vector Operations (`simd4`)**: **3.57x faster** throughput over dynamic loops by unrolling 4-lane arithmetic and dot products.
- **Cartesian Loops (`A x B`)**: **1.05x faster** (lowers to C-accelerated `itertools.product`).
- **Nullish Coalescing (`??`)**: **1.04x faster** (inlined into Python 3.12 `POP_JUMP_IF_NONE` bytecode, executing in 20.03 ms vs Python's 20.76 ms).
- **Destructuring (`{ a, b }`)**: **0.98x parity** (direct tuple/subscript unpacking).

---

## 4. When Is It Slightly Slower? (The Cost of Safety)

Safe navigation (`user?.profile?.name`) evaluates safely when properties are `None`.
- Raw Python (`user.profile.name`) executes in ~50 nanoseconds via direct `LOAD_ATTR`, but crashes with `AttributeError` if any value is `None`.
- Radical wraps the access safely, taking ~59 nanoseconds.
- **The difference is only 9 nanoseconds**—an intentional trade-off to eliminate production `NoneType` crashes.

---

## 5. `radical build` vs `radical run` & Bytecode Caching

- **`radical run script.rad`**: Automatically caches compiled bytecode in `__radcache__/<name>.pyc` verified against file SHA-256 hash and compiler version. Warm runs start in **~33 ms** (near instant).
- **`radical build script.rad -o script.py`**: Compiles Ahead-of-Time (AOT). The generated `.py` file has **zero compilation overhead** at runtime. Best for production deployments and Docker containers.

---

## 6. Compile-Time Constant Folding

Radical features an AST-level constant folder (`RadicalConstantFolder`). Constant mathematical expressions are pre-evaluated at compile time:

```radical
# Source:
const SECONDS_PER_DAY = 24 * 60 * 60

# Transpiled Output:
SECONDS_PER_DAY = 86400
```

- Pre-computes arithmetic binary operations (`+`, `-`, `*`, `/`, `//`, `**`, `%`) and bitwise operations (`<<`, `>>`, `&`, `|`, `^`).
- Zero runtime arithmetic overhead.

---

## 7. Native Fast Tier (`native fn`)

For critical inner loops, `native fn` provides access to JIT fastmath acceleration:

```radical
native fn l2_norm(x: float, y: float) -> float:
    return (x * x + y * y) ** 0.5
```

- When Numba is available in your environment, `@_rad_native` compiles functions down to LLVM machine code.
- Functions execute at native C speeds without interpreter loop overhead.

---

## 8. Memory Arenas vs Python GC Overhead

Allocating hundreds of thousands of small objects in standard Python forces the cyclic garbage collector to maintain object headers and run generational sweeps.

- **`arena(capacity)`**: Groups allocations into a single continuous buffer.
- Individual allocations are simple pointer increments ($O(1)$).
- Memory reclamation upon block exit is a single reset of the arena offset ($O(1)$), completely bypassing GC tracking.

---

## 9. Diagnostic Visibility: `radical explain`

Understand what optimizations are occurring under the hood without inspecting generated code:

```bash
radical explain script.rad
```

Sample output:
```text
=== Radical Compiler Diagnostics: script.rad ===
Line 12: Pipeline fused -> comprehension (2.79x faster)
Line 25: Parallel loop -> multi-core worker pool
Line 38: Constant folded: 24 * 60 * 60 -> 86400
Line 45: Native fn 'l2_norm' -> JIT fastmath tier enabled
Line 52: Memory arena allocated (1048576 bytes) -> O(1) bulk deallocation
```

---

## 10. The Three Execution Tiers

Radical structures code into three distinct execution tiers to balance rapid prototyping with bare-metal speed:

| Tier | Declaration | Safety & Features | Runtime Engine | Fallback |
| :--- | :--- | :--- | :--- | :--- |
| **Tier 1: Dynamic Python** | Standard Python / `let` / `const` | Full Python dynamic ergonomics, duck typing, PyPI ecosystem | Standard CPython 3.10+ VM | None needed |
| **Tier 2: Checked Radical** | `fn`, `struct`, `trait`, `Result`/`Option` | Compile-time signature checks, immutable slots, exhaustive error flow | Optimized Python Bytecode | Standard Python |
| **Tier 3: Restricted Native** | `native fn`, `buffer[T]`, `unsafe:` | Zero dynamic allocations, unboxed numeric arrays, hardware alignment | Numba JIT / LLVM compilation | Typed CPU fallback |

---

## 11. Continuous Hardware-Aligned Typed Buffers

Radical's `buffer[T](size, aligned=N)` provides contiguous physical memory:
- **Zero-Copy Slicing:** `buf[a..b]` creates borrowed slices without copying underlying bytes.
- **Hardware Alignment:** `aligned=64` aligns pointers to 64-byte boundaries for AVX-512 and Apple Silicon cache-line efficiency.
- **Buffer Protocol:** `buf.to_memoryview()` exposes zero-copy NumPy and PyTorch interop without overhead.

---

## 12. Developer Tooling & Static Safety (`radical fmt`, `radical lint`)

- **`radical fmt [-w]`**: Deterministic canonical code formatter for Radical syntax.
- **`radical lint`**: Static pointer analysis that verifies pointers extracted via `.ptr` inside an `unsafe:` block never leak or get dereferenced outside unsafe scopes.


