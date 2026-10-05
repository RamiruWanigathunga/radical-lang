# Lesson 04: Range Literals & Cartesian Matrix Loops

## 1. The Problem in Python: Verbose Ranges & Deep Loop Nesting

Nested loops in Python chew up horizontal indentation and execute slow interpreter loops. Furthermore, `range()` cannot express inclusive upper bounds without manually computing `(stop + 1)`:
```python
# Standard Python: 3 levels of indentation
coords = []
for z in range(depth):
    for y in range(height):
        for x in range(width):
            coords.append((x, y, z))
```

---

## 2. 3-Way Code Comparison

### Radical Source (`.rad`)
```radical
# 1. Flat multi-dimensional Cartesian loops
let grid = []
for x, y in (0..width x 0..height):
    grid.append((x, y))

# 2. Inclusive range literal (1 <= n <= 10)
for i in 1..=10:
    print(i)

# 3. Stepped range literal
const evens = [i for i in 0..=20..2]
```

### Equivalent Standard Python
```python
# 1. Deeply indented nested loops
grid = []
for x in range(0, width):
    for y in range(0, height):
        grid.append((x, y))

# 2. Manual + 1 calculation for inclusive range
for i in range(1, 10 + 1):
    print(i)

# 3. range with step
evens = [i for i in range(0, 20 + 1, 2)]
```

### Transpiled Python Output (`radical build`)
```python
import itertools

grid = []
# Uses compiled C itertools.product for flat, fast iteration
for x, y in itertools.product(range(0, width), range(0, height)):
    grid.append((x, y))

for i in range(1, (10) + 1):
    print(i)

evens = [i for i in range(0, (20) + 1, 2)]
```

---

## 3. Range Syntax Summary

| Interval | Radical (`.rad`) | Transpiled Python |
| :--- | :--- | :--- |
| Exclusive $[0, 10)$ | `0..10` | `range(0, 10)` |
| Inclusive $[1, 10]$ | `1..=10` | `range(1, (10) + 1)` |
| Stepped $[0, 10)$ by 2 | `0..10..2` | `range(0, 10, 2)` |
| Inclusive Stepped $[1, 10]$ by 2 | `1..=10..2` | `range(1, (10) + 1, 2)` |

---

## 4. Cartesian Product (`x`) Dimensions

You can chain Cartesian iterations across arbitrary dimensions:
```radical
# 3D Matrix Iteration
for x, y, z in (0..X_MAX x 0..Y_MAX x 0..Z_MAX):
    process_voxel(x, y, z)

# Transpiles directly to:
for x, y, z in itertools.product(range(0, X_MAX), range(0, Y_MAX), range(0, Z_MAX)):
    process_voxel(x, y, z)
```
- `itertools.product` runs in **compiled C** inside CPython, reducing interpreter loop dispatch overhead by **1.05x**.
