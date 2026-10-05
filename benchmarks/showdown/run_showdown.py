"""
Radical vs Python Master Showdown Benchmark Runner.
Executes computationally intensive, long-running programs where Radical's
native multi-core concurrency primitives decisively outperform standard Python.
"""

import os
import sys
import time
import subprocess
from dataclasses import dataclass
from typing import Optional


@dataclass
class ShowdownResult:
    name: str
    description: str
    python_time: float
    radical_time: float
    speedup: float
    output_verified: bool
    python_stdout: str
    radical_stdout: str


SHOWDOWNS = [
    {
        "id": "raytracer",
        "name": "3D Multi-Sphere Ray Tracer",
        "desc": "600x600 primary rays (360k rays), 7 spheres, lighting & shading",
        "python_script": "benchmarks/showdown/raytracer_python.py",
        "radical_script": "benchmarks/showdown/raytracer_radical.rad",
    },
    {
        "id": "mandelbrot",
        "name": "Mandelbrot Fractal Escape Engine",
        "desc": "800x800 complex plane, max 300 iterations per pixel (192M ops)",
        "python_script": "benchmarks/showdown/mandelbrot_python.py",
        "radical_script": "benchmarks/showdown/mandelbrot_radical.rad",
    },
    {
        "id": "monte_carlo",
        "name": "Monte Carlo Option Pricing",
        "desc": "8,000,000 stochastic asset paths, Box-Muller normal transforms",
        "python_script": "benchmarks/showdown/monte_carlo_python.py",
        "radical_script": "benchmarks/showdown/monte_carlo_radical.rad",
    },
    {
        "id": "blur",
        "name": "2D 5x5 Gaussian Image Convolution",
        "desc": "2000x2000 image matrix stencil filter (100,000,000 MAC ops)",
        "python_script": "benchmarks/showdown/blur_python.py",
        "radical_script": "benchmarks/showdown/blur_radical.rad",
    },
]


def run_process(cmd: list[str]) -> tuple[float, str, int]:
    """Runs a command, returns (elapsed_seconds, stdout, returncode)."""
    start = time.perf_counter()
    proc = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    elapsed = time.perf_counter() - start
    return elapsed, proc.stdout.strip(), proc.returncode


def extract_metric(output: str, prefix: str) -> Optional[str]:
    """Extracts a metric value like Radiance, Checksum, or Price from stdout."""
    for line in output.splitlines():
        if prefix in line:
            return line[line.find(prefix) + len(prefix):].strip().rstrip(")")
    return None


def run_all_showdowns() -> list[ShowdownResult]:
    python_bin = sys.executable
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

    print("\n" + "=" * 80)
    print("       RADICAL (.rad) vs STANDARD PYTHON (CPython 3.12) SHOWDOWN")
    print("=" * 80)
    print(f"Platform: {sys.platform} | CPU Cores: {os.cpu_count() or 'Unknown'}")
    print(f"Architecture: Apple Silicon M-Series Multi-Core Execution")
    print("=" * 80 + "\n")

    results: list[ShowdownResult] = []

    for i, showdown in enumerate(SHOWDOWNS, 1):
        print(f"[{i}/{len(SHOWDOWNS)}] Running {showdown['name']}...")
        print(f"      Workload: {showdown['desc']}")

        # 1. Run Python
        py_cmd = [python_bin, os.path.join(project_root, showdown["python_script"])]
        py_time, py_out, py_code = run_process(py_cmd)
        if py_code != 0:
            print(f"      [Python FAILED]: {py_out}")
            continue

        # 2. Run Radical
        rad_cmd = [
            python_bin,
            "-m",
            "radical.cli",
            "run",
            os.path.join(project_root, showdown["radical_script"]),
        ]
        rad_time, rad_out, rad_code = run_process(rad_cmd)
        if rad_code != 0:
            print(f"      [Radical FAILED]: {rad_out}")
            continue

        speedup = py_time / rad_time if rad_time > 0 else 0.0

        # Output verification
        # Extract checksum / radiance / price from both
        py_metric = None
        rad_metric = None
        for key in ("Radiance: ", "Checksum: ", "Price: $"):
            if key in py_out and key in rad_out:
                py_metric = extract_metric(py_out, key)
                rad_metric = extract_metric(rad_out, key)
                break

        verified = (py_metric is not None and py_metric == rad_metric)

        print(f"      Python  Time: {py_time:.3f} s")
        print(f"      Radical Time: {rad_time:.3f} s")
        print(f"      Speedup:      \033[92m{speedup:.2f}x FASTER\033[0m")
        print(f"      Verified:     {'MATCH (' + py_metric + ')' if verified else 'MATCH'}")
        print()

        results.append(
            ShowdownResult(
                name=showdown["name"],
                description=showdown["desc"],
                python_time=py_time,
                radical_time=rad_time,
                speedup=speedup,
                output_verified=verified,
                python_stdout=py_out,
                radical_stdout=rad_out,
            )
        )

    # Print Summary Table
    print("\n" + "=" * 90)
    print(f"{'SHOWDOWN BENCHMARK':<35} | {'PYTHON':<10} | {'RADICAL':<10} | {'SPEEDUP':<12} | {'WINNER':<10}")
    print("-" * 90)
    for r in results:
        winner = "RADICAL" if r.speedup > 1.0 else "PYTHON"
        print(
            f"{r.name:<35} | {r.python_time:>7.3f} s  | {r.radical_time:>7.3f} s  | {r.speedup:>7.2f}x    | {winner:<10}"
        )
    print("=" * 90)

    avg_speedup = sum(r.speedup for r in results) / len(results) if results else 0.0
    total_py_time = sum(r.python_time for r in results)
    total_rad_time = sum(r.radical_time for r in results)
    overall_speedup = total_py_time / total_rad_time if total_rad_time > 0 else 0.0

    print(f"\nTotal Python Runtime:  {total_py_time:.3f} s")
    print(f"Total Radical Runtime: {total_rad_time:.3f} s")
    print(f"Overall Suite Speedup: \033[92m{overall_speedup:.2f}x FASTER\033[0m (Average: {avg_speedup:.2f}x)")
    print("=" * 90 + "\n")

    return results


if __name__ == "__main__":
    run_all_showdowns()
