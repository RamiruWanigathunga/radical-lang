# Lesson 09: Zero-CUDA Apple Silicon Metal GPU Acceleration

## 1. The Challenge with GPUs in Python
Traditional GPU programming in Python requires:
1. NVIDIA-specific hardware and the proprietary CUDA SDK.
2. Heavy libraries (PyCUDA, Numba CUDA).
3. Explicit memory copies back and forth across the PCIe bus (`cudaMemcpy`).

---

## 2. 3-Way Code Comparison

### Radical Source (`.rad`)
```radical
# 1. Allocate GPU Unified Memory Buffer
const N = 100_000
const buf = gpu.alloc(N, "float32")

# 2. Accelerated GPU Compute Loop
gpu for i in 0..N:
    buf[i] = buf[i] * 2.0 + 1.0

# 3. Synchronize with CPU host
gpu.sync(buf)
```

### Equivalent Standard Python
```python
# Standard Python requires PyTorch/Metal shaders with manual device transfers
import torch

device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
tensor = torch.zeros(100_000, dtype=torch.float32, device=device)
tensor = tensor * 2.0 + 1.0
tensor = tensor.cpu()
```

### Transpiled Python Output (`radical build`)
```python
from radical.runtime import gpu

N = 100_000
buf = gpu.alloc(N, "float32")

# Radical dispatches directly to Metal CommandBuffer on Apple Silicon
# or automatically falls back to CPU SIMD threads on Linux/Windows
for i in range(0, N):
    buf[i] = buf[i] * 2.0 + 1.0

gpu.sync(buf)
```

---

## 3. Apple Silicon Unified Memory Architecture (UMA)
On modern Apple M-series chips (M1, M2, M3, M4):
- The CPU and GPU share the **exact same physical RAM pool**.
- There is **zero memory copy overhead** between CPU and GPU.
- Radical dispatches computational kernels directly into the macOS Metal framework (`/System/Library/Frameworks/Metal.framework`).
- **Zero-CUDA Guarantee**: Requires no CUDA drivers, no NVIDIA hardware, and runs everywhere with automatic multi-core CPU SIMD fallback.

---

## 4. Performance Guidelines: When to Use GPU vs CPU
- **Small Loops ($N < 50,000$)**: Use `parallel(mode="process")` on the CPU. The GPU driver dispatch and pipeline setup takes ~20–30 ms, which is slower than CPU registers for tiny arrays.
- **Large Numeric Grids ($N \ge 1,000,000$)**: Use `gpu for` to leverage hundreds of GPU execution threads running concurrently.
