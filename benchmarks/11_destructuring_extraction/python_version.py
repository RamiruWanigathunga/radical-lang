# Benchmark 11: Python Subscript Record Extraction

records = [
    {"id": i, "name": f"user_{i}", "score": i * 1.5, "role": "admin" if i % 2 == 0 else "guest"}
    for i in range(25000)
]

def extract_records(items):
    total_score = 0.0
    admin_count = 0
    for r in items:
        # Standard python dictionary key lookup
        uid = r["id"]
        uname = r["name"]
        uscore = r["score"]
        urole = r["role"]
        total_score += uscore
        if urole == "admin":
            admin_count += 1
    return total_score, admin_count

score, admins = extract_records(records)
print(f"Total score: {score:.1f}, Admins: {admins}")
