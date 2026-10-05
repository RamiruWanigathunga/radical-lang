# Benchmark 01: Python Sequential Heavy Math Computation

def is_prime(n: int) -> bool:
    if n <= 1:
        return False
    if n <= 3:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def compute():
    count = 0
    for n in range(1, 30000):
        if is_prime(n):
            count += 1
    return count

res = compute()
print(f"Primes counted: {res}")
