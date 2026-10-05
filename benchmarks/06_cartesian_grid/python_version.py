# Benchmark 06: Python Nested Loops Coordinate Grid

def compute_grid(w: int, h: int) -> float:
    total_dist = 0.0
    for x in range(w):
        for y in range(h):
            total_dist += (x * x + y * y) ** 0.5
    return total_dist

res = compute_grid(300, 300)
print(f"Total grid distance: {res:.2f}")
