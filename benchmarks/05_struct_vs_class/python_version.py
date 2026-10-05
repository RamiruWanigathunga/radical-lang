# Benchmark 05: Standard Python Class Instantiation & Access

class Point:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

def run():
    total = 0.0
    for i in range(25000):
        p = Point(float(i), float(i + 1))
        total += p.x * p.x + p.y * p.y
    return total

res = run()
print(f"Total distance sum: {res:.1f}")
