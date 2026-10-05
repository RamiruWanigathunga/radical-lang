"""
Showdown 04: Standard Python Single-Core 2D 5x5 Gaussian Image Convolution.
Performs a 2D 5x5 stencil filter on a 2000x2000 image matrix (100,000,000 MAC ops).
"""

import time

W = 2000
H = 2000
IMAGE = [[(x * y) % 256 for x in range(W)] for y in range(H)]

WEIGHTS = (
    (1, 4, 6, 4, 1),
    (4, 16, 24, 16, 4),
    (6, 24, 36, 24, 6),
    (4, 16, 24, 16, 4),
    (1, 4, 6, 4, 1),
)

def blur_row(y: int) -> int:
    r_slice = [IMAGE[y + dy] for dy in range(-2, 3)]
    row_sum = 0
    for x in range(2, W - 2):
        acc = 0
        for dy in range(5):
            r = r_slice[dy]
            w = WEIGHTS[dy]
            acc += r[x-2]*w[0] + r[x-1]*w[1] + r[x]*w[2] + r[x+1]*w[3] + r[x+2]*w[4]
        row_sum += (acc >> 8)
    return row_sum

def main():
    print(f"[Python] Starting 2D 5x5 Gaussian Image Convolution ({W}x{H} = {W*H:,} pixels)...")

    start = time.perf_counter()
    total_val = 0
    for y in range(2, H - 2):
        total_val += blur_row(y)
    elapsed = time.perf_counter() - start

    print(f"[Python] Finished in {elapsed:.3f} s (Checksum: {total_val})")
    return elapsed

if __name__ == "__main__":
    main()
