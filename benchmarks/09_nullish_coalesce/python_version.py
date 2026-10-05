# Benchmark 09: Python Ternary Null Checking

values = [None if i % 2 == 0 else i for i in range(50000)]

def run_coalesce(items):
    resolved = []
    for item in items:
        # Standard python safe check preserving 0
        val = item if item is not None else 999
        resolved.append(val)
    return resolved

res = run_coalesce(values)
print(f"Coalesced {len(res)} items, sum: {sum(res)}")
