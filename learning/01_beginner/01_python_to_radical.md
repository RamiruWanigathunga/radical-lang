# Lesson 01: Python to Radical & The Superset Rule

## 1. The Core Guarantee
**Every line of valid Python 3.10+ code is 100% valid Radical code.**

You do not need to rewrite your libraries, learn a new object model, or abandon PyPI:
```radical
# Valid Radical code (it's just Python!)
import math
import numpy as np

def greet(name: str) -> str:
    return f"Hello, {name}!"

print(greet("World"))
```

---

## 2. The Toolchain

Radical provides five essential CLI tools:

### A. Run (`radical run`)
Executes `.rad` files directly in memory with zero disk writes, utilizing SHA-256 bytecode caching:
```bash
radical run app.rad
```

### B. Explain (`radical explain`)
Inspects compiler optimizations, pipeline fusions, parallel loops, constant folding, and backend tiers:
```bash
radical explain app.rad
radical explain app.rad -v
```

### C. Build (`radical build`)
Transpiles Radical into clean, standard Python 3.10+ code for production:
```bash
radical build app.rad -o dist/app.py
```
*The output requires only standard Python to run. There is zero vendor lock-in.*

### D. Check (`radical check`)
Verifies syntax, type annotations, and `const` invariants without executing:
```bash
radical check app.rad
```

### E. REPL (`radical repl`)
Interactive command line shell:
```bash
$ radical repl
rad> [1, 2, 3] |> map((x) => x * 10, _) |> list
[10, 20, 30]
```

---

## 3. Performance Note
When running `radical build`, the resulting `.py` script runs on the standard Python interpreter at **100% native speed** with zero transpilation overhead. Radical also performs compile-time constant folding and AST optimization.
