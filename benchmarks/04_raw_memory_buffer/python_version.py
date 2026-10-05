# Benchmark 04: Python Boxed List Allocation & Mutation

SIZE = 5000000
PASSES = 120

# Allocate list of boxed integers
buf = [0] * SIZE

# Sequential indexed mutation
for _ in range(PASSES):
    for i in range(SIZE):
        buf[i] = (i * 7) % 256

total = sum(buf)
print(f"Memory sum: {total}")
