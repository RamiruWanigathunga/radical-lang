# Radical Code Examples Catalog

This directory contains 16 verified, production-ready code examples showcasing the syntax, ergonomic additions, and systems-performance primitives of the **Radical (`.rad`)** programming language.

Every example is standalone and tested with `radical run`.

---

## Catalog Overview

```text
examples/
├── 01_beginner/
│   ├── 01_pipeline_data_flow.rad
│   ├── 02_safe_navigation_coalescing.rad
│   ├── 03_ranges_and_comprehensions.rad
│   ├── 04_let_and_const_bindings.rad
│   └── 05_object_destructuring.rad
├── 02_intermediate/
│   ├── 01_slotted_structs_and_copy_with.rad
│   ├── 02_algebraic_data_types_enums.rad
│   ├── 03_error_handling_result.rad
│   ├── 04_resource_management_defer_using.rad
│   └── 05_cartesian_matrix_coordinates.rad
└── 03_advanced/
    ├── 01_multicore_parallel_processing.rad
    ├── 02_hardware_simd_vector_math.rad
    ├── 03_continuous_buffers_and_unsafe.rad
    ├── 04_channels_and_select_concurrency.rad
    ├── 05_zero_cuda_apple_metal_gpu.rad
    └── 06_native_fastmath_jit.rad
```

---

## 1. Beginner Tier: Modern Ergonomics

These examples teach the core syntax additions that make Radical code more concise and expressive than standard Python.

| Example | Primary Constructs | Description |
| :--- | :--- | :--- |
| **`01_pipeline_data_flow.rad`** | `\|>`, `=>`, `_` | Transforms inverted nested function calls into linear left-to-right pipelines with pipeline step fusion into list comprehensions. |
| **`02_safe_navigation_coalescing.rad`** | `?.`, `?[]`, `??`, `??=` | Demonstrates null-safe object attribute and dictionary traversal, and strict nullish coalescing preserving `0`, `False`, and `""`. |
| **`03_ranges_and_comprehensions.rad`** | `0..N`, `1..=N`, `0..N..step` | Rust/Swift style numeric ranges eliminating off-by-one errors in loops and comprehensions. |
| **`04_let_and_const_bindings.rad`** | `const`, `let` | Explicit mutable state accumulators (`let`) versus compile-time verified immutable symbols (`const`). |
| **`05_object_destructuring.rad`** | `{ a, b } = target` | Simultaneous unpacking of object attributes and dictionary keys without repetitive subscript boilerplate. |

**Run Beginner Examples:**
```bash
radical run examples/01_beginner/01_pipeline_data_flow.rad
radical run examples/01_beginner/02_safe_navigation_coalescing.rad
radical run examples/01_beginner/03_ranges_and_comprehensions.rad
radical run examples/01_beginner/04_let_and_const_bindings.rad
radical run examples/01_beginner/05_object_destructuring.rad
```

---

## 2. Intermediate Tier: Types, Safety, and Resource Management

These examples demonstrate structured types, functional immutability, error propagation, and resource cleanup.

| Example | Primary Constructs | Description |
| :--- | :--- | :--- |
| **`01_slotted_structs_and_copy_with.rad`** | `struct`, `with { ... }` | Slotted value records with 3x memory reduction and non-destructive functional copy-updates. |
| **`02_algebraic_data_types_enums.rad`** | `enum Name: Variant(...)` | Tagged union variants for state machines and robust pattern matching (`match / case`). |
| **`03_error_handling_result.rad`** | `Result[T, E]`, `?` operator | Rust-style zero-cost error propagation returning `Ok` / `Err` and unwrapping with `?`. |
| **`04_resource_management_defer_using.rad`** | `defer`, `using` | Deterministic LIFO cleanup handlers (`defer`) and scoped RAII resource blocks (`using`). |
| **`05_cartesian_matrix_coordinates.rad`** | `for x, y in (A x B):` | Multi-dimensional grid and matrix traversal without nested indentation bloat. |

**Run Intermediate Examples:**
```bash
radical run examples/02_intermediate/01_slotted_structs_and_copy_with.rad
radical run examples/02_intermediate/02_algebraic_data_types_enums.rad
radical run examples/02_intermediate/03_error_handling_result.rad
radical run examples/02_intermediate/04_resource_management_defer_using.rad
radical run examples/02_intermediate/05_cartesian_matrix_coordinates.rad
```

---

## 3. Advanced Tier: High-Performance Systems & Hardware Acceleration

These examples demonstrate Radical's systems programming primitives, hardware vectorization, and multi-core / GPU acceleration.

| Example | Primary Constructs | Description |
| :--- | :--- | :--- |
| **`01_multicore_parallel_processing.rad`** | `parallel for` | Distributes CPU-bound loops across multi-core worker pools, bypassing Python's GIL. |
| **`02_hardware_simd_vector_math.rad`** | `simd[float, 4]`, `.dot()`, `.sum()` | Hardware-aligned 4-lane vector registers for physics and game-engine math. |
| **`03_continuous_buffers_and_unsafe.rad`** | `buffer[T]`, `unsafe:` | Unboxed cache-line aligned contiguous memory with zero-copy slicing and scoped unchecked pointer reads/writes. |
| **`04_channels_and_select_concurrency.rad`** | `chan[T]`, `select:` | Go-style thread-safe ring-buffer channels and non-blocking multi-branch channel polling. |
| **`05_zero_cuda_apple_metal_gpu.rad`** | `gpu for`, `gpu.alloc()` | Dispatches parallel compute shaders on Apple Silicon GPUs via Metal with CPU SIMD fallback. |
| **`06_native_fastmath_jit.rad`** | `native fn` | Unlocks LLVM fastmath compilation and JIT acceleration for inner numerical kernels. |

**Run Advanced Examples:**
```bash
radical run examples/03_advanced/01_multicore_parallel_processing.rad
radical run examples/03_advanced/02_hardware_simd_vector_math.rad
radical run examples/03_advanced/03_continuous_buffers_and_unsafe.rad
radical run examples/03_advanced/04_channels_and_select_concurrency.rad
radical run examples/03_advanced/05_zero_cuda_apple_metal_gpu.rad
radical run examples/03_advanced/06_native_fastmath_jit.rad
```

---

## Inspecting Compiler Optimizations

You can use the Radical diagnostic tools on any example file:

```bash
# Check syntax and const immutability:
radical check examples/01_beginner/01_pipeline_data_flow.rad

# Explain pipeline fusion and target lowerings:
radical explain -v examples/01_beginner/01_pipeline_data_flow.rad

# Transpile to clean standard Python:
radical build examples/01_beginner/01_pipeline_data_flow.rad -o output.py
```
