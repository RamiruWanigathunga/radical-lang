# Benchmark 02: Standard Python 4-Lane Vector Dot Product

def run_dot_products():
    total = 0.0
    for i in range(10000):
        # 4-lane vector representation in Python
        a = [float(i), float(i + 1), float(i + 2), float(i + 3)]
        b = [2.0, 3.0, 4.0, 5.0]
        # Dot product: sum(x*y for x, y in zip(a, b))
        dot = a[0] * b[0] + a[1] * b[1] + a[2] * b[2] + a[3] * b[3]
        total += dot
    return total

res = run_dot_products()
print(f"Total vector dot sum: {res:.1f}")
