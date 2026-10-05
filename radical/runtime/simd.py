"""
Radical Language Runtime: Hardware SIMD Vectors.
Hardware-aligned vector registers supporting element-wise operations and reductions.
"""

from typing import Any, Callable, Sequence


class SIMDVector:
    """
    Hardware-aligned SIMD vector representing contiguous lanes of numeric data.
    """
    __slots__ = ("_dtype", "_width", "_data", "x", "y", "z", "w")

    def __init__(self, dtype: type, width: int, values: Sequence[Any]) -> None:
        self._dtype = dtype
        self._width = width
        if len(values) == 1 and width > 1:
            self._data = [dtype(values[0])] * width
        elif len(values) == width:
            self._data = [dtype(v) for v in values]
        else:
            raise ValueError(f"Expected {width} values or 1 scalar for SIMD[{dtype.__name__}, {width}], got {len(values)}")
        if width == 4:
            self.x = self._data[0]
            self.y = self._data[1]
            self.z = self._data[2]
            self.w = self._data[3]

    def __len__(self) -> int:
        return self._width

    def __getitem__(self, idx: int) -> Any:
        return self._data[idx]

    def __setitem__(self, idx: int, val: Any) -> None:
        self._data[idx] = self._dtype(val)

    def __add__(self, other: Any) -> "SIMDVector":
        if isinstance(other, SIMDVector):
            if self._width != other._width:
                raise ValueError("SIMD vector widths must match for addition")
            a, b = self._data, other._data
            if self._width == 4:
                return SIMDVector(self._dtype, 4, (a[0] + b[0], a[1] + b[1], a[2] + b[2], a[3] + b[3]))
            return SIMDVector(self._dtype, self._width, [x + y for x, y in zip(a, b)])
        a = self._data
        if self._width == 4:
            return SIMDVector(self._dtype, 4, (a[0] + other, a[1] + other, a[2] + other, a[3] + other))
        return SIMDVector(self._dtype, self._width, [x + other for x in a])

    def __sub__(self, other: Any) -> "SIMDVector":
        if isinstance(other, SIMDVector):
            if self._width != other._width:
                raise ValueError("SIMD vector widths must match for subtraction")
            a, b = self._data, other._data
            if self._width == 4:
                return SIMDVector(self._dtype, 4, (a[0] - b[0], a[1] - b[1], a[2] - b[2], a[3] - b[3]))
            return SIMDVector(self._dtype, self._width, [x - y for x, y in zip(a, b)])
        a = self._data
        if self._width == 4:
            return SIMDVector(self._dtype, 4, (a[0] - other, a[1] - other, a[2] - other, a[3] - other))
        return SIMDVector(self._dtype, self._width, [x - other for x in a])

    def __mul__(self, other: Any) -> "SIMDVector":
        if isinstance(other, SIMDVector):
            if self._width != other._width:
                raise ValueError("SIMD vector widths must match for multiplication")
            a, b = self._data, other._data
            if self._width == 4:
                return SIMDVector(self._dtype, 4, (a[0] * b[0], a[1] * b[1], a[2] * b[2], a[3] * b[3]))
            return SIMDVector(self._dtype, self._width, [x * y for x, y in zip(a, b)])
        a = self._data
        if self._width == 4:
            return SIMDVector(self._dtype, 4, (a[0] * other, a[1] * other, a[2] * other, a[3] * other))
        return SIMDVector(self._dtype, self._width, [x * other for x in a])

    def __truediv__(self, other: Any) -> "SIMDVector":
        if isinstance(other, SIMDVector):
            if self._width != other._width:
                raise ValueError("SIMD vector widths must match for division")
            a, b = self._data, other._data
            if self._width == 4:
                return SIMDVector(self._dtype, 4, (a[0] / b[0], a[1] / b[1], a[2] / b[2], a[3] / b[3]))
            return SIMDVector(self._dtype, self._width, [x / y for x, y in zip(a, b)])
        a = self._data
        if self._width == 4:
            return SIMDVector(self._dtype, 4, (a[0] / other, a[1] / other, a[2] / other, a[3] / other))
        return SIMDVector(self._dtype, self._width, [x / other for x in a])

    def dot(self, other: "SIMDVector") -> Any:
        """Computes the dot product of two SIMD vectors."""
        if self._width != other._width:
            raise ValueError("SIMD vector widths must match for dot product")
        if self._width == 4:
            return self.x * other.x + self.y * other.y + self.z * other.z + self.w * other.w
        return sum(x * y for x, y in zip(self._data, other._data))

    def sum(self) -> Any:
        """Reduces the vector by summing all lanes."""
        if self._width == 4:
            return self.x + self.y + self.z + self.w
        return sum(self._data)

    def to_list(self) -> list[Any]:
        return list(self._data)

    @property
    def lanes(self) -> list[Any]:
        return list(self._data)

    def __repr__(self) -> str:
        return f"simd[{self._dtype.__name__}, {self._width}]({', '.join(repr(x) for x in self._data)})"


class _SIMDFactory:
    """Provides Mojo-style `simd[dtype, width](*vals)` syntax and direct `simd(vals)` calls."""
    def __init__(self) -> None:
        self._cache: dict[tuple[type, int], Callable[..., SIMDVector]] = {}

    def __getitem__(self, item: tuple[type, int]) -> Callable[..., SIMDVector]:
        cached = self._cache.get(item)
        if cached is not None:
            return cached
        dtype, width = item
        def creator(*vals: Any) -> SIMDVector:
            return SIMDVector(dtype, width, vals)
        self._cache[item] = creator
        return creator

    def __call__(self, *args: Any) -> SIMDVector:
        if not args:
            raise ValueError("simd requires at least one argument")
        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            raw_vals = list(args[0])
        else:
            raw_vals = list(args)
        if not raw_vals:
            raise ValueError("simd requires non-empty sequence")
        dtype = type(raw_vals[0])
        return SIMDVector(dtype, len(raw_vals), raw_vals)


simd = _SIMDFactory()
