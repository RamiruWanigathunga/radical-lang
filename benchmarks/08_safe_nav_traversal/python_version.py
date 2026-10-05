# Benchmark 08: Python Safe Traversal with Null Guards

data = [
    {"user": {"profile": {"address": {"city": "Tokyo"}}}} if i % 3 == 0 else
    ({"user": {"profile": None}} if i % 3 == 1 else {})
    for i in range(15000)
]

def traverse(items):
    cities = []
    for item in items:
        # Standard defensive python navigation
        u = item.get("user") if isinstance(item, dict) else None
        p = u.get("profile") if isinstance(u, dict) else None
        a = p.get("address") if isinstance(p, dict) else None
        c = a.get("city") if isinstance(a, dict) else None
        cities.append(c if c is not None else "Unknown")
    return cities

res = traverse(data)
print(f"Traversed {len(res)} items. Unknown count: {res.count('Unknown')}")
