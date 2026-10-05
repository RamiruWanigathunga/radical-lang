# Contributing to Radical

Thank you for your interest in contributing to **Radical**! We welcome bug reports, feature proposals, documentation improvements, runtime optimizations, and code contributions.

This document provides guidelines and instructions for contributing to the Radical codebase.

---

## 1. Code of Conduct

All contributors and maintainers are expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please read it before participating in discussions or opening pull requests.

---

## 2. Development Setup

### 2.1 Prerequisites
- Python 3.10, 3.11, or 3.12
- Git
- `pip` / `venv`
- (Optional) Apple Silicon Mac for Metal GPU development (`pyobjc-framework-Metal`)
- (Optional) Numba for `native fn` JIT acceleration

### 2.2 Local Environment Setup
```bash
# 1. Clone the repository
git clone https://github.com/RamiruWanigathunga/radical-lang.git
cd radical-lang

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install development dependencies and install Radical in editable mode
pip install -e ".[dev]"
```

---

## 3. Running the Test Suite

We require all pull requests to pass the full test suite without regressions.

```bash
# Run all unit and integration tests
pytest

# Run tests with verbose output
pytest -v

# Run specific feature tests
pytest tests/test_pipeline.py
pytest tests/test_v2_features.py
```

### 3.1 Verifying Examples
Run the full suite of beginner, intermediate, and advanced examples:
```bash
for f in examples/*/*.rad; do
    radical run "$f" || exit 1
done
```

### 3.2 Running the Benchmarks
To verify performance across the 12 benchmark suites:
```bash
python benchmarks/run_all.py
```

---

## 4. Code Style & Architecture

### 4.1 Superset Invariant
Radical is a **strict superset of Python 3.10+**:
- Never break standard Python syntax compatibility.
- Ensure new syntactic forms lower cleanly to standard Python 3.10+ AST nodes without requiring custom CPython runtime modifications.

### 4.2 Code Organization
- **Compiler Passes** reside under `radical/transforms/`:
  - Keep transformations single-responsibility (e.g., `functional.py`, `concurrency.py`, `operators.py`).
  - Preserve source coordinate mapping (`line` and `col`) across token transformations for accurate diagnostics.
- **Runtime Primitives** reside under `radical/runtime/`:
  - Runtime helpers must be lightweight, type-stable, and importable without heavy external dependencies.
- **Tools & CLI** reside under `radical/tools/` and `radical/cli.py`.

### 4.3 Formatting & Linting
Radical includes its own formatting and linting tools:
```bash
# Format your Radical code
radical fmt -w file.rad

# Lint your Radical code for safety
radical lint file.rad
```

---

## 5. Submitting a Pull Request (PR)

1. **Fork & Branch**: Create a branch off `main` with a descriptive name (e.g., `feat/pipeline-indexing` or `fix/arrow-lexer`).
2. **Write Tests**: Add corresponding test coverage under `tests/test_<feature>.py`.
3. **Document**: Update relevant documentation in `docs/` and add an example in `examples/` if introducing user-facing syntax.
4. **Self-Review**: Verify `pytest` passes and no temporary files (`__pycache__`, `__radcache__`, `.DS_Store`) are committed.
5. **Open PR**: Use our [Pull Request Template](.github/PULL_REQUEST_TEMPLATE.md) and describe your changes clearly.
