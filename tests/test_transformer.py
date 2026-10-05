"""
Tests for RadicalTranspiler: End-to-end multi-pass source transformation.
"""

import pytest
from radical.transformer import RadicalTranspiler
from radical.exceptions import RadicalCompileError


def test_standard_python_passthrough():
    code = '''
def greet(name: str) -> str:
    msg = f"Hello, {name}!"
    return msg

result = greet("World")
'''
    transpiler = RadicalTranspiler(filename="test.rad")
    emitted = transpiler.transpile(code)
    assert "def greet" in emitted
    
    # Execute emitted code
    namespace = {}
    exec(emitted, namespace)
    assert namespace["result"] == "Hello, World!"


def test_pipeline_and_arrow_and_coalesce():
    code = '''
const base = None
const fallback = 10
const initial = base ?? fallback

calc = (x) => x * 3 + 2

const final_val = initial |> calc
'''
    transpiler = RadicalTranspiler(filename="test.rad")
    emitted = transpiler.transpile(code)
    
    namespace = {}
    exec(emitted, namespace)
    assert namespace["final_val"] == 32


def test_struct_and_fn_and_simd():
    code = '''
struct Point(x: float, y: float)

fn distance_sq(p: Point) -> float:
    return p.x * p.x + p.y * p.y

pt = Point(3.0, 4.0)
dist = distance_sq(pt)
vec = simd([1.0, 2.0, 3.0, 4.0]) * 2.0
'''
    transpiler = RadicalTranspiler(filename="test.rad")
    emitted = transpiler.transpile(code)
    
    assert "@dataclass" in emitted
    assert "slots" in emitted and "frozen" in emitted
    assert "class Point:" in emitted
    assert "def distance_sq" in emitted
    
    namespace = {}
    exec(emitted, namespace)
    assert namespace["dist"] == 25.0
    assert namespace["vec"].lanes == [2.0, 4.0, 6.0, 8.0]


def test_cartesian_and_parallel():
    code = '''
pairs = []
for x, y in (0..3 x 0..2):
    pairs.append((x, y))

results = []
parallel for i in 0..5:
    results.append(i * 10)
'''
    transpiler = RadicalTranspiler(filename="test.rad")
    emitted = transpiler.transpile(code)
    
    assert "import itertools" in emitted
    assert "itertools.product" in emitted
    assert "_rad_parallel_for" in emitted
    
    namespace = {}
    exec(emitted, namespace)
    assert len(namespace["pairs"]) == 6
    assert sorted(namespace["results"]) == [0, 10, 20, 30, 40]


def test_destructuring_and_defer():
    code = '''
const data = {"user": "Alice", "role": "Admin"}
const { user, role } = data

events = []
def run():
    defer events.append("cleaned up")
    events.append("active")

run()
'''
    transpiler = RadicalTranspiler(filename="test.rad")
    emitted = transpiler.transpile(code)
    
    namespace = {}
    exec(emitted, namespace)
    assert namespace["user"] == "Alice"
    assert namespace["role"] == "Admin"
    assert namespace["events"] == ["active", "cleaned up"]


def test_const_reassignment_raises_compile_error():
    code = '''
const API_URL = "https://api.radical.lang"
API_URL = "https://hacked.com"
'''
    transpiler = RadicalTranspiler(filename="test_const_err.rad")
    with pytest.raises(RadicalCompileError) as exc_info:
        transpiler.transpile(code)
    
    assert "Cannot reassign constant 'API_URL'" in str(exc_info.value)
