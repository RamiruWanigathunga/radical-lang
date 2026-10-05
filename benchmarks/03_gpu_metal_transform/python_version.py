# Benchmark 03: Python Sequential Array Transformation

N = 25000

input_arr = [float(i) for i in range(N)]
output_arr = [0.0] * N

for i in range(N):
    output_arr[i] = input_arr[i] * 3.5 + 2.0

print(f"Transformed {N} items. Sample [100]: {output_arr[100]}")
