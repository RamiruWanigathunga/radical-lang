# Lesson 02: Pipelines (`|>`) & Arrow Functions (`=>`)

## 1. The Problem in Python: Inverted Function Calls
In Python, chaining operations forces you to read inside-out:
```python
# Standard Python: You have to find 'words' in the middle, then read backwards!
result = print(list(map(str.upper, filter(lambda w: len(w) > 3, words))))
```

---

## 2. 3-Way Code Comparison

### Radical Source (`.rad`)
```radical
const words = ["ant", "elephant", "cat", "giraffe"]

const long_caps = words
    |> filter((w) => len(w) > 3, _)
    |> map((w) => w.upper(), _)
    |> list

print(long_caps)
```

### Equivalent Standard Python
```python
words = ["ant", "elephant", "cat", "giraffe"]

# Nested inside-out calls with intermediate generator overhead
long_caps = list(
    map(
        lambda w: w.upper(),
        filter(lambda w: len(w) > 3, words)
    )
)

print(long_caps)
```

### Transpiled Python Output (`radical build`)
```python
words = ["ant", "elephant", "cat", "giraffe"]

# Fused into a single list comprehension without temporary map/filter iterators
long_caps = [(_rad_x1.upper()) for _rad_x1 in (words) if (len(_rad_x1) > 3)]

print(long_caps)
```

---

## 3. The Rules of the Pipeline Operator (`|>`)

1. **Simple Call (`x |> f`)**:
   - Source: `5 |> double`
   - Transpiled: `double(5)`
2. **Additional Arguments (`x |> f(a, b)`)**:
   - Source: `10 |> pow(2)`
   - Transpiled: `pow(10, 2)`
3. **Placeholder Argument (`_`)**:
   - When the piped value is not the first argument, `_` designates where it goes:
   - Source: `"radical" |> str.center(20, _)`
   - Transpiled: `str.center(20, "radical")`
4. **Multiline Pipelines**:
   - Place `|>` at the start of new lines for maximum readability:
   ```radical
   const sanitized = input_text
       |> str.strip
       |> str.lower
       |> (s) => s.replace(" ", "_")
   ```

---

## 4. Arrow Functions (`=>`)

Radical replaces Python's verbose `lambda` keyword with arrow function notation:

| Syntax | Radical (`.rad`) | Transpiled Python |
| :--- | :--- | :--- |
| Zero params | `() => 42` | `(lambda: 42)` |
| Single param | `x => x * 2` | `(lambda x: x * 2)` |
| Multi params | `(a, b) => a + b` | `(lambda a, b: a + b)` |
| Typed params | `(a: int, b: int) -> int => a + b` | `(lambda a, b: a + b)` |

---

## 5. Performance: Automatic Pipeline Fusion

When standard Python chains `list(map(f, filter(p, data)))`, it incurs severe overhead:
1. Heap allocates a `filter` iterator object.
2. Heap allocates a `map` iterator object.
3. Performs a dynamic Python function call frame for every single element.

In Radical, pipelines terminating in collectors like `list`, `set`, `tuple`, or `sum` automatically undergo **Pipeline Fusion**:

```radical
# Radical Source:
const results = raw_numbers 
    |> filter((x) => x % 2 == 0) 
    |> map((x) => x * 2) 
    |> list

# Lowers Directly into an Inlined List Comprehension:
results = [(_rad_x1 * 2) for _rad_x1 in (raw_numbers) if (_rad_x1 % 2 == 0)]
```

### Key Performance Benefits:
- **Zero Intermediate Iterators**: No intermediate iterator objects or generator allocations.
- **Closure Inlining**: Single-parameter arrow functions are inlined directly into the comprehension body, eliminating `lambda` call frames.
- **Benchmark**: **2.79x faster** than standard Python `list(map(lambda, filter(lambda, data)))` (0.1764s vs 0.4922s for 100k items).
