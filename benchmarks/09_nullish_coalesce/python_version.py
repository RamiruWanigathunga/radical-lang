# Benchmark 09: Python Ternary Null Checking

values = [None if i % 2 == 0 else i for i in range(5000000)]
PASSES = 240

def run_coalesce(items):
    total = 0
    for _ in range(PASSES):
        for item in items:
            # Standard python safe check preserving 0
            val = item if item is not None else 999
            total += val
    return total

res = run_coalesce(values)
print(f"Coalesced {len(values) * PASSES} items, sum: {res}")
