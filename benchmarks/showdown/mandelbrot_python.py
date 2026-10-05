"""
Showdown 02: Standard Python Single-Core Mandelbrot Fractal Engine.
Computes 800x800 complex plane (up to 300 iterations per pixel = 192M ops).
"""

import time

def escape_count(cr: float, ci: float, max_iter: int = 300) -> int:
    zr = 0.0
    zi = 0.0
    zr2 = 0.0
    zi2 = 0.0
    for i in range(max_iter):
        if zr2 + zi2 > 4.0:
            return i
        zi = 2.0 * zr * zi + ci
        zr = zr2 - zi2 + cr
        zr2 = zr * zr
        zi2 = zi * zi
    return max_iter

def compute_row(y: int, width: int = 800, height: int = 800, max_iter: int = 300) -> int:
    ci = -1.25 + (y / height) * 2.5
    row_sum = 0
    dx = 2.5 / width
    xmin = -2.0
    for x in range(width):
        cr = xmin + x * dx
        row_sum += escape_count(cr, ci, max_iter)
    return row_sum

def main():
    WIDTH = 800
    HEIGHT = 800
    print(f"[Python] Starting Mandelbrot Engine ({WIDTH}x{HEIGHT}, max_iter=300)...")

    start = time.perf_counter()
    total = 0
    for y in range(HEIGHT):
        total += compute_row(y, WIDTH, HEIGHT)
    elapsed = time.perf_counter() - start

    print(f"[Python] Finished in {elapsed:.3f} s (Checksum: {total})")
    return elapsed

if __name__ == "__main__":
    main()
