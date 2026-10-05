# Benchmark 12: Python Sequential Mandelbrot Fractal (100x100)

WIDTH = 100
HEIGHT = 100
MAX_ITER = 80

def compute_pixel(c_real: float, c_imag: float, max_iter: int) -> int:
    z_real = 0.0
    z_imag = 0.0
    for iter_count in range(max_iter):
        zr2 = z_real * z_real
        zi2 = z_imag * z_imag
        if zr2 + zi2 > 4.0:
            return iter_count
        z_imag = 2.0 * z_real * z_imag + c_imag
        z_real = zr2 - zi2 + c_real
    return max_iter

def compute_fractal():
    total_escapes = 0
    for y in range(HEIGHT):
        c_imag = -1.2 + (y / HEIGHT) * 2.4
        for x in range(WIDTH):
            c_real = -2.0 + (x / WIDTH) * 2.5
            total_escapes += compute_pixel(c_real, c_imag, MAX_ITER)
    return total_escapes

escapes = compute_fractal()
print(f"Total Mandelbrot escape iterations: {escapes}")
