# Benchmark 10: Python Sequential Matrix Multiplication (900x900)

N = 900
A = [[float(i + j) for j in range(N)] for i in range(N)]
B = [[float(i * 2 + j) for j in range(N)] for i in range(N)]
C = [[0.0 for _ in range(N)] for _ in range(N)]

for i in range(N):
    for j in range(N):
        s = 0.0
        for k in range(N):
            s += A[i][k] * B[k][j]
        C[i][j] = s

total = sum(sum(row) for row in C)
print(f"Matrix mult sum (size {N}x{N}): {total:.1f}")
