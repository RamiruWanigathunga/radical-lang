"""
Showdown 03: Standard Python Single-Core Monte Carlo Financial Simulation.
Simulates 8,000,000 stochastic asset paths with Box-Muller normal transforms
to price European call options under Black-Scholes dynamics.
"""

import math
import time

def simulate_batch(batch_idx: int, count: int = 100_000) -> float:
    # LCG PRNG with distinct seed per batch
    state = 123456789 + batch_idx * 10007
    s0 = 100.0
    k = 105.0
    r = 0.05
    sigma = 0.2
    t = 1.0
    drift = (r - 0.5 * sigma * sigma) * t
    vol = sigma * math.sqrt(t)

    payoff_sum = 0.0
    for _ in range(count):
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        u1 = (state + 0.5) / 4294967296.0
        state = (state * 1664525 + 1013904223) & 0xFFFFFFFF
        u2 = (state + 0.5) / 4294967296.0
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(6.283185307179586 * u2)
        st = s0 * math.exp(drift + vol * z)
        payoff = st - k if st > k else 0.0
        payoff_sum += payoff
    return payoff_sum

def main():
    num_batches = 80
    paths_per_batch = 100_000
    total_paths = num_batches * paths_per_batch
    print(f"[Python] Starting Monte Carlo Simulation ({total_paths:,} stochastic asset paths)...")

    start = time.perf_counter()
    total_payoff = 0.0
    for b in range(num_batches):
        total_payoff += simulate_batch(b, paths_per_batch)
    
    price = (total_payoff / total_paths) * math.exp(-0.05)
    elapsed = time.perf_counter() - start

    print(f"[Python] Finished in {elapsed:.3f} s (Fair Call Price: ${price:.4f})")
    return elapsed

if __name__ == "__main__":
    main()
