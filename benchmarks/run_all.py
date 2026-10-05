"""
Executes the complete Radical vs Standard Python 12-Benchmark Suite.
Saves markdown and JSON reports.
"""

import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from benchmarks.benchmark_runner import BenchmarkRunner, BenchmarkResult


def main() -> None:
    benchmarks_dir = Path(__file__).parent
    runner = BenchmarkRunner(runs=5, warmup=2)

    benchmark_configs = [
        ("01_parallel_compute", "Multi-Core Prime Count", "Parallelism & Threading"),
        ("02_simd_vector_dot", "4-Lane SIMD Vector Dot Product", "Hardware SIMD"),
        ("03_gpu_metal_transform", "Zero-CUDA Apple Metal GPU Transform", "GPU Acceleration"),
        ("04_raw_memory_buffer", "Continuous Raw Ctypes Buffer vs List", "Memory Architecture"),
        ("05_struct_vs_class", "Slotted Frozen Struct vs Python Class", "Memory & OOP"),
        ("06_cartesian_grid", "Cartesian Matrix Coordinate Loop", "Iteration & Loops"),
        ("07_pipeline_etl", "Data Pipeline ETL Chaining vs Inverted Calls", "Pipelines & Ergonomics"),
        ("08_safe_nav_traversal", "Deep Safe Traversal vs Defensive If-Checks", "Safe Navigation"),
        ("09_nullish_coalesce", "Nullish Coalescing (??) vs Ternary None Check", "Coalescing"),
        ("10_matrix_multiplication", "Matrix Multiplication (80x80)", "Parallel Linear Algebra"),
        ("11_destructuring_extraction", "Destructuring Assignment vs Subscripts", "Destructuring"),
        ("12_mandelbrot_fractal", "Mandelbrot Fractal Computation (100x100)", "Parallelism & Numerics"),
    ]

    results: list[BenchmarkResult] = []

    print("==================================================================")
    print("      RADICAL (.rad) vs STANDARD PYTHON BENCHMARK SUITE")
    print("==================================================================")

    for subdir, name, category in benchmark_configs:
        bench_path = benchmarks_dir / subdir
        py_file = bench_path / "python_version.py"
        rad_file = bench_path / "radical_version.rad"

        if not py_file.exists() or not rad_file.exists():
            print(f"Skipping {subdir}: missing script files.")
            continue

        result = runner.run_benchmark(
            name=name,
            category=category,
            python_script=py_file,
            radical_script=rad_file,
        )
        results.append(result)

    # Generate Markdown Report
    report_md = runner.generate_markdown_report(results)
    out_file = benchmarks_dir / "BENCHMARK_RESULTS.md"
    out_file.write_text(report_md, encoding="utf-8")
    print("\n==================================================================")
    print(f"Benchmark run complete! Results written to:\n  {out_file}")
    print("==================================================================")
    print("\n" + report_md)


if __name__ == "__main__":
    main()
