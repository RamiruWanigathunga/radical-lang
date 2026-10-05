# Lesson 07: Multi-Core Parallel Computing (Bypassing the GIL)

## 1. The CPython GIL Dilemma
In standard Python, the **Global Interpreter Lock (GIL)** restricts execution to a single CPU thread. Even on a machine with 10 or 16 CPU cores:
- Standard `for` loops use exactly **1 CPU core** (100% capacity on 1 core, 0% on all others).
- `threading.Thread` or `ThreadPoolExecutor` are blocked by the GIL for compute tasks.
- `multiprocessing` requires 20+ lines of process pool boilerplate, pickling setups, and chunk management.

---

## 2. 3-Way Code Comparison

### Radical Source (`.rad`)
```radical
# 1. Multi-Core Parallel Loop (Auto-infers mode="process" on assignment)
const squares = parallel for i in 0..10_000:
    return i * i

# 2. Parallel List Comprehension
const rendered_rows = parallel [render_scanline(y) for y in 0..HEIGHT]
```

### Equivalent Standard Python
```python
import multiprocessing

def _worker_fn(i):
    return i * i

# 15+ lines of multiprocessing boilerplate, chunking, and context management
with multiprocessing.get_context("fork").Pool() as pool:
    squares = pool.map(_worker_fn, range(0, 10_000), chunksize=100)
```

### Transpiled Python Output (`radical build`)
```python
from radical.runtime import _rad_parallel_for, _rad_parallel_comp

# Dispatches across CPU cores via Unix Copy-On-Write without pickling overhead
squares = _rad_parallel_for(
    range(0, 10_000),
    lambda i: i * i,
    mode="process"
)

rendered_rows = _rad_parallel_comp(
    lambda y: render_scanline(y),
    range(0, HEIGHT)
)
```

---

## 3. How Radical Achieves 5x Speedups Over Python

When you specify `mode="process"`:
1. **Unix Copy-On-Write (COW)**: Uses `multiprocessing.get_context("fork")` on Unix/macOS. Large read-only input structures (like matrices or images) are shared between CPU cores **instantly with zero data copying**.
2. **Auto-Chunking**: Automatically calculates optimal batch sizes (`chunk_size`) so worker processes spend time computing rather than synchronizing IPC queues.
3. **Multi-Core Scaling**: Engages all CPU cores simultaneously (e.g., 11 cores on Apple Silicon M3 Pro).

### Benchmark Showdown Results:
- **3D Ray Tracer**: Python 1.417s $\rightarrow$ Radical **0.316s** (**4.49x faster**)
- **Mandelbrot Fractal**: Python 2.758s $\rightarrow$ Radical **0.527s** (**5.24x faster**)
- **Monte Carlo Pricing**: Python 2.591s $\rightarrow$ Radical **0.505s** (**5.13x faster**)
- **2D Image Convolution**: Python 4.083s $\rightarrow$ Radical **0.856s** (**4.77x faster**)
