# Benchmark 03: Python Sequential Array Transformation

N = 5000000
PASSES = 90

input_arr = [float(i % 1000) for i in range(N)]
output_arr = [0.0] * N

for _ in range(PASSES):
    for i in range(N):
        output_arr[i] = input_arr[i] * 3.5 + 2.0

print(f"Transformed {N} items. Sample [100]: {output_arr[100]}")
