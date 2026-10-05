# Benchmark 08: Python Safe Traversal with Null Guards

data = [
    {"user": {"profile": {"address": {"city": "Tokyo"}}}} if i % 3 == 0 else
    ({"user": {"profile": None}} if i % 3 == 1 else {})
    for i in range(1000000)
]
PASSES = 140

def traverse(items):
    tokyo_count = 0
    for _ in range(PASSES):
        for item in items:
            # Standard defensive python navigation
            u = item.get("user") if isinstance(item, dict) else None
            p = u.get("profile") if isinstance(u, dict) else None
            a = p.get("address") if isinstance(p, dict) else None
            c = a.get("city") if isinstance(a, dict) else None
            if c == "Tokyo":
                tokyo_count += 1
    return tokyo_count

res = traverse(data)
print(f"Traversed {len(data) * PASSES} items. Tokyo count: {res}")
