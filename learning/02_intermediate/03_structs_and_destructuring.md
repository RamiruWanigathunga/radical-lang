# Lesson 06: Slotted Structs, Traits, Enums & Error Propagation

## 1. Slotted Structs (`struct`) & Copy-Update (`with`)

### The Problem in Python
Standard Python classes generate an instance dictionary (`__dict__`), consuming ~150-200 bytes of heap memory per instance. Modifying immutable dataclasses requires verbose `replace(obj, ...)` imports.

### 3-Way Code Comparison

#### Radical Source (`.rad`)
```radical
# 1. Slotted, frozen value type
struct Point(x: float, y: float)

# 2. Immutable functional copy-update
const p1 = Point(1.0, 2.0)
const p2 = p1 with { x: 50.0 } # Point(x=50.0, y=2.0)

# 3. Fast destructuring
const { x, y } = p2
```

#### Equivalent Standard Python
```python
from dataclasses import dataclass, replace

@dataclass(slots=True, frozen=True)
class Point:
    x: float
    y: float

p1 = Point(1.0, 2.0)
p2 = replace(p1, x=50.0)

x = p2.x
y = p2.y
```

#### Transpiled Python Output (`radical build`)
```python
from dataclasses import dataclass
from radical.runtime import _rad_copy_with

@dataclass(slots=True, frozen=True)
class Point:
    x: float
    y: float

p1 = Point(1.0, 2.0)
p2 = _rad_copy_with(p1, x=50.0)

_rad_destruct_1 = p2
x = _rad_destruct_1["x"] if isinstance(_rad_destruct_1, dict) else getattr(_rad_destruct_1, "x")
y = _rad_destruct_1["y"] if isinstance(_rad_destruct_1, dict) else getattr(_rad_destruct_1, "y")
```

---

## 2. Structural Traits (`trait`)

Radical provides first-class structural typing via `trait`:

#### Radical Source (`.rad`)
```radical
trait Serializable:
    def serialize(self) -> str: ...

struct User(id: int, name: str):
    def serialize(self) -> str:
        return f'{{"id": {self.id}, "name": "{self.name}"}}'

# Structural typing works without explicit inheritance
let u = User(1, "Alice")
print(isinstance(u, Serializable)) # True
```

#### Transpiled Python Output (`radical build`)
```python
import typing

@typing.runtime_checkable
class Serializable(typing.Protocol):
    def serialize(self) -> str:
        ...
```

---

## 3. Algebraic Data Types (`enum`) & Exhaustive Matching

Radical provides Rust-style sum types / tagged unions:

#### Radical Source (`.rad`)
```radical
enum Shape:
    Circle(radius: float)
    Rectangle(width: float, height: float)

fn calculate_area(s: Shape) -> float:
    match s:
        case Shape.Circle(r):
            return 3.14159 * r * r
        case Shape.Rectangle(w, h):
            return w * h
```

#### Transpiled Python Output (`radical build`)
```python
from dataclasses import dataclass

class Shape: pass

@dataclass(frozen=True)
class Circle(Shape):
    radius: float
Shape.Circle = Circle

@dataclass(frozen=True)
class Rectangle(Shape):
    width: float
    height: float
Shape.Rectangle = Rectangle
```

---

## 4. Rust-Style Error Propagation (`?`)

Eliminate nested `try...except` and unwrap `Result` or `Option` safely:

#### Radical Source (`.rad`)
```radical
fn parse_port(s: str) -> Result[int, str]:
    if s.isdigit():
        return Result.Ok(int(s))
    return Result.Err("Port must be numeric")

fn start_server(port_str: str) -> Result[int, str]:
    let port = parse_port(port_str)? # Early returns Result.Err if invalid!
    return Result.Ok(port)
```

#### Transpiled Python Output (`radical build`)
```python
from radical.runtime import Result, Ok, Err

def parse_port(s: str) -> Result[int, str]:
    if s.isdigit():
        return Result.Ok(int(s))
    return Result.Err("Port must be numeric")

def start_server(port_str: str) -> Result[int, str]:
    _rad_try_tmp_1 = parse_port(port_str)
    if hasattr(_rad_try_tmp_1, 'is_err') and _rad_try_tmp_1.is_err():
        return _rad_try_tmp_1
    if hasattr(_rad_try_tmp_1, 'is_none') and _rad_try_tmp_1.is_none():
        return _rad_try_tmp_1
    port = getattr(_rad_try_tmp_1, 'value', _rad_try_tmp_1)
    return Result.Ok(port)
```

> **Compile-Time Contract**: When using `?` inside a function with a return annotation, the return type must be `Result[...]` or `Option[...]`. Annotating a scalar like `-> int` raises a compile error.
