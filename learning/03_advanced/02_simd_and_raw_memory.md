# Lesson 08: Systems Memory, SIMD, Channels & Native Functions

## 1. Mojo-Style SIMD Vectors (`simd4`)

Radical brings hardware-vectorized Single Instruction, Multiple Data (SIMD) primitives directly into Python's syntax.

### 3-Way Code Comparison

#### Radical Source (`.rad`)
```radical
const v1 = simd[float, 4](1.0, 2.0, 3.0, 4.0)
const v2 = simd[float, 4](10.0, 20.0, 30.0, 40.0)

const v_sum = v1 + v2        # simd[float, 4](11.0, 22.0, 33.0, 44.0)
const dot_prod = v1.dot(v2)  # 300.0 (3.57x faster than Python loop)
```

#### Equivalent Standard Python
```python
# Unrolled manually or dynamic zip loops with interpreter overhead
v1 = [1.0, 2.0, 3.0, 4.0]
v2 = [10.0, 20.0, 30.0, 40.0]

v_sum = [a + b for a, b in zip(v1, v2)]
dot_prod = sum(a * b for a, b in zip(v1, v2))
```

#### Transpiled Python Output (`radical build`)
```python
from radical.runtime import simd

v1 = simd[float, 4](1.0, 2.0, 3.0, 4.0)
v2 = simd[float, 4](10.0, 20.0, 30.0, 40.0)

v_sum = v1 + v2
dot_prod = v1.dot(v2)
```

---

## 2. Hardware-Aligned Continuous Buffers (`buffer[T]`) & Scoped `unsafe:`

### 3-Way Code Comparison

#### Radical Source (`.rad`)
```radical
# 1. 64-byte hardware cache-line aligned continuous float buffer
let buf = buffer[f32](1024, aligned=64)
buf[0] = 3.14159
let slice = buf[0..10]               # Zero-copy borrowed slice!
let memview = buf.to_memoryview()    # Zero-copy Python buffer protocol

# 2. Scoped unsafe block for raw pointer reads & writes
unsafe:
    let ptr = buf.ptr
    let val = ptr.read[f32](0)        # Typed pointer read
    ptr.write[f32](0, val * 2.0)      # Typed pointer write
    ptr.write_unchecked(1, 2.71828)   # Unchecked write

# 3. Scoped bump allocation arena (bulk O(1) free upon exit)
using a = arena(1024 * 1024):
    let chunk = a.alloc(512)
```

#### Equivalent Standard Python
```python
import ctypes

# Complex ctypes memory allocation, manual offset calculations, and manual freeing
raw_array = (ctypes.c_float * 1024)()
raw_array[0] = 3.14159
# Manual pointer manipulation without safety boundaries
```

#### Transpiled Python Output (`radical build`)
```python
from radical.runtime import buffer, arena, _rad_unsafe_context, f32

buf = buffer[f32](1024, aligned=64)
buf[0] = 3.14159
slice = buf[range(0, 10)]
memview = buf.to_memoryview()

with _rad_unsafe_context():
    ptr = buf.ptr
    val = ptr.read[f32](0)
    ptr.write[f32](0, val * 2.0)
    ptr.write_unchecked(1, 2.71828)

with arena(1024 * 1024) as a:
    chunk = a.alloc(512)
```

---

## 3. Concurrency Channels (`chan`) and `select:` Blocks

#### Radical Source (`.rad`)
```radical
let ch = chan[str](10)
ch.send("task ready")

select:
    case msg = ch.recv():
        print("Worker received:", msg)
    default:
        print("No tasks pending")
```

#### Transpiled Python Output (`radical build`)
```python
from radical.runtime import chan

ch = chan[str](10)
ch.send("task ready")

_rad_sel_1 = False
if not _rad_sel_1:
    _rad_ok_2, _rad_tmp_2 = ch.try_recv()
    if _rad_ok_2:
        msg = _rad_tmp_2
        _rad_sel_1 = True
        print("Worker received:", msg)
if not _rad_sel_1:
    print("No tasks pending")
```

---

## 4. The Restricted Native Tier (`native fn`)

For compute kernels, `native fn` compiles down to machine code with Numba fastmath:

#### Radical Source (`.rad`)
```radical
native fn dot_product(a: buffer[f32], b: buffer[f32], n: int) -> f32:
    let acc: f32 = 0.0
    for i in 0..n:
        acc += a[i] * b[i]
    return acc
```

#### Transpiled Python Output (`radical build`)
```python
from radical.runtime import _rad_native, buffer, f32

@_rad_native
def dot_product(a: buffer[f32], b: buffer[f32], n: int) -> f32:
    acc: f32 = 0.0
    for i in range(0, n):
        acc += a[i] * b[i]
    return acc
```
