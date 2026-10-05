"""
Radical Language AST Node Definitions.
Represents Radical-specific syntactic constructs before lowering to Python AST.
"""

from dataclasses import dataclass, field
from typing import Any, Optional, Sequence


@dataclass
class RadicalNode:
    """Base class for all Radical AST nodes."""
    lineno: int = 1
    col_offset: int = 0


# --- Expressions ---

@dataclass
class RangeExpr(RadicalNode):
    """Represents a range literal: start..end or start..=end with optional step."""
    start: Any = None
    end: Any = None
    step: Any = None
    inclusive: bool = False


@dataclass
class CoalesceExpr(RadicalNode):
    """Represents nullish coalescing: left ?? right."""
    left: Any = None
    right: Any = None


@dataclass
class SafeAttrExpr(RadicalNode):
    """Represents safe attribute access: value?.attr."""
    value: Any = None
    attr: str = ""


@dataclass
class SafeIndexExpr(RadicalNode):
    """Represents safe indexing: value?[index]."""
    value: Any = None
    index: Any = None


@dataclass
class SafeCallExpr(RadicalNode):
    """Represents safe function call: func?.(*args, **kwargs)."""
    func: Any = None
    args: list[Any] = field(default_factory=list)
    keywords: list[Any] = field(default_factory=list)


@dataclass
class ArrowFunctionExpr(RadicalNode):
    """Represents an arrow function: (a, b) => expr."""
    params: list[str] = field(default_factory=list)
    body: Any = None


@dataclass
class PipeExpr(RadicalNode):
    """Represents a pipeline operation: left |> right."""
    left: Any = None
    right: Any = None


@dataclass
class CopyWithExpr(RadicalNode):
    """Represents functional copy-update: target with { field: val }."""
    target: Any = None
    updates: dict[str, Any] = field(default_factory=dict)


@dataclass
class TaggedTemplateExpr(RadicalNode):
    """Represents tagged template literal: tag"template string {expr}"."""
    tag: str = ""
    template: str = ""


@dataclass
class TryOperatorExpr(RadicalNode):
    """Represents error propagation: expr?."""
    expr: Any = None


@dataclass
class SIMDVectorExpr(RadicalNode):
    """Represents 4-lane hardware SIMD vector: simd[float, 4](...)."""
    dtype: str = "float32"
    lanes: list[Any] = field(default_factory=list)


# --- Statements & Declarations ---

@dataclass
class CoalesceAssignStmt(RadicalNode):
    """Represents nullish coalesce assignment: target ??= value."""
    target: str = ""
    value: Any = None


@dataclass
class ConstDeclStmt(RadicalNode):
    """Represents an immutable binding: const ident = value."""
    target: Any = None
    value: Any = None


@dataclass
class LetDeclStmt(RadicalNode):
    """Represents a mutable binding: let ident = value."""
    target: Any = None
    value: Any = None


@dataclass
class DestructureStmt(RadicalNode):
    """Represents object/dict destructuring: const { a, b } = res."""
    targets: list[str] = field(default_factory=list)
    source: Any = None
    is_const: bool = False


@dataclass
class StructField:
    """Represents a field in a struct declaration."""
    name: str
    type_annotation: Optional[str] = None
    default_value: Optional[str] = None


@dataclass
class StructDefStmt(RadicalNode):
    """Represents a struct declaration: struct Point(x: float, y: float)."""
    name: str = ""
    fields: list[StructField] = field(default_factory=list)
    body_lines: list[str] = field(default_factory=list)


@dataclass
class TraitDefStmt(RadicalNode):
    """Represents structural trait interface: trait Serializable: ..."""
    name: str = ""
    methods: list[str] = field(default_factory=list)


@dataclass
class EnumVariant:
    """Represents an ADT variant in an enum definition."""
    name: str
    fields: list[StructField] = field(default_factory=list)


@dataclass
class EnumDefStmt(RadicalNode):
    """Represents an algebraic data type: enum Shape: Circle(...) Rectangle(...)."""
    name: str = ""
    variants: list[EnumVariant] = field(default_factory=list)


@dataclass
class NativeFnDefStmt(RadicalNode):
    """Represents restricted fastmath tier function: native fn dot(...) -> f32: ..."""
    name: str = ""
    args: list[tuple[str, str]] = field(default_factory=list)
    return_type: Optional[str] = None
    body: list[Any] = field(default_factory=list)


@dataclass
class CartesianLoopStmt(RadicalNode):
    """Represents a Cartesian loop: for x, y in (A x B): body."""
    targets: list[str] = field(default_factory=list)
    iterables: list[Any] = field(default_factory=list)
    body: list[Any] = field(default_factory=list)


@dataclass
class ParallelLoopStmt(RadicalNode):
    """Represents a parallel loop: parallel for item in items: body."""
    target: str = ""
    iterable: Any = None
    body: list[Any] = field(default_factory=list)
    max_workers: Optional[int] = None


@dataclass
class GPUForStmt(RadicalNode):
    """Represents Apple Silicon GPU compute loop: gpu for i in 0..N: body."""
    target: str = ""
    start: Any = None
    end: Any = None
    body: list[Any] = field(default_factory=list)


@dataclass
class DeferStmt(RadicalNode):
    """Represents deferred execution: defer cleanup()."""
    statement: str = ""


@dataclass
class UsingStmt(RadicalNode):
    """Represents scoped resource management: using res = expr: body."""
    target: str = ""
    expression: Any = None
    body: list[Any] = field(default_factory=list)


@dataclass
class UnsafeBlockStmt(RadicalNode):
    """Represents scoped unsafe pointer boundary: unsafe: body."""
    body: list[Any] = field(default_factory=list)


@dataclass
class SelectCase:
    """Represents a branch in a select: block."""
    channel_recv_expr: Any = None
    target_var: Optional[str] = None
    body: list[Any] = field(default_factory=list)


@dataclass
class SelectStmt(RadicalNode):
    """Represents non-blocking channel polling: select: case ...: default: ..."""
    cases: list[SelectCase] = field(default_factory=list)
    default_body: Optional[list[Any]] = None


@dataclass
class RawBufferStmt(RadicalNode):
    """Represents a native continuous buffer: raw buf[1024]: body."""
    name: str = ""
    size: Any = None
    dtype: str = "c_uint8"
    body: list[Any] = field(default_factory=list)
