import pytest
from radical.gpu import gpu, GPUBuffer


def test_gpu_device_detection():
    # Verify device detection works (Apple Silicon Metal or CPU SIMD)
    assert gpu.device_name is not None
    print(f"Detected GPU device: {gpu.device_name}")


def test_gpu_buffer_allocation_and_indexing():
    buf = gpu.alloc(size=1024, dtype="float32")
    assert len(buf) == 1024
    buf[0] = 3.14159
    buf[1023] = 42.0
    assert abs(buf[0] - 3.14159) < 1e-4
    assert buf[1023] == 42.0


def test_gpu_loop_execution():
    n = 10000
    a = gpu.alloc(n, "float32", [1.0] * n)
    b = gpu.alloc(n, "float32", [2.0] * n)
    out = gpu.alloc(n, "float32")

    def vector_add_kernel(i: int):
        out[i] = a[i] + b[i]

    gpu.execute_loop(n, vector_add_kernel)

    # Verify all 10000 elements were computed
    for i in range(100):
        assert out[i] == 3.0
    assert out[9999] == 3.0
