# Benchmark 02: Standard Python 4-Lane Vector Dot Product

N = 1000000
STEPS = 350

# Pre-streamed 4-lane vector dataset (e.g. vertices / physics particles)
vectors = [[float(i % 100), float((i + 1) % 100), float((i + 2) % 100), float((i + 3) % 100)] for i in range(N)]
weights = [2.0, 3.0, 4.0, 5.0]

def run_dot_products():
    total = 0.0
    w0, w1, w2, w3 = weights[0], weights[1], weights[2], weights[3]
    for _ in range(STEPS):
        for v in vectors:
            total += v[0] * w0 + v[1] * w1 + v[2] * w2 + v[3] * w3
    return total

res = run_dot_products()
print(f"Total vector dot sum: {res:.1f}")
