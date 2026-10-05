"""
Radical Language Runtime: Memory and Typed Buffers.
Provides first-class typed contiguous memory buffers backed by ctypes,
zero-copy slicing, raw pointer views, and bump memory arenas.
"""

import ctypes
from typing import Any, Callable
from radical.runtime.unsafe import _rad_is_unsafe_active


# Type alias identifiers for typed buffer declaration: buffer[u8](10)
u8 = "u8"
uint8 = "u8"
byte = "u8"
i8 = "i8"
int8 = "i8"
u16 = "u16"
uint16 = "u16"
i16 = "i16"
int16 = "i16"
u32 = "u32"
uint32 = "u32"
i32 = "i32"
int32 = "i32"
u64 = "u64"
uint64 = "u64"
i64 = "i64"
int64 = "i64"
f16 = "f16"
f32 = "f32"
float32 = "f32"
f64 = "f64"
float64 = "f64"

DTYPE_CTYPES: dict[str, Any] = {
    "u8": ctypes.c_uint8, "uint8": ctypes.c_uint8, "byte": ctypes.c_uint8,
    "i8": ctypes.c_int8, "int8": ctypes.c_int8,
    "u16": ctypes.c_uint16, "uint16": ctypes.c_uint16,
    "i16": ctypes.c_int16, "int16": ctypes.c_int16,
    "u32": ctypes.c_uint32, "uint32": ctypes.c_uint32,
    "i32": ctypes.c_int32, "int32": ctypes.c_int32, "int": ctypes.c_int32,
    "u64": ctypes.c_uint64, "uint64": ctypes.c_uint64,
    "i64": ctypes.c_int64, "int64": ctypes.c_int64,
    "f16": ctypes.c_uint16,  # 16-bit half precision raw representation (2 bytes)
    "f32": ctypes.c_float, "float32": ctypes.c_float, "float": ctypes.c_float,
    "f64": ctypes.c_double, "float64": ctypes.c_double, "double": ctypes.c_double,
}

DTYPE_FORMAT: dict[str, str] = {
    "u8": "B", "uint8": "B", "byte": "B",
    "i8": "b", "int8": "b",
    "u16": "H", "uint16": "H",
    "i16": "h", "int16": "h",
    "u32": "I", "uint32": "I",
    "i32": "i", "int32": "i", "int": "i",
    "u64": "Q", "uint64": "Q",
    "i64": "q", "int64": "q",
    "f16": "H",
    "f32": "f", "float32": "f", "float": "f",
    "f64": "d", "float64": "d", "double": "d",
}


class BufferSlice:
    """Zero-copy slice view into a contiguous TypedBuffer."""
    __slots__ = ("_parent", "_start", "_end", "size")

    def __init__(self, parent: "TypedBuffer", start: int, end: int) -> None:
        self._parent = parent
        self._start = start
        self._end = end
        self.size = max(0, end - start)

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, idx: int) -> Any:
        if idx < 0 or idx >= self.size:
            raise IndexError(f"BufferSlice index {idx} out of bounds (size {self.size})")
        return self._parent[self._start + idx]

    def __setitem__(self, idx: int, val: Any) -> None:
        if idx < 0 or idx >= self.size:
            raise IndexError(f"BufferSlice index {idx} out of bounds (size {self.size})")
        self._parent[self._start + idx] = val

    def to_list(self) -> list[Any]:
        return [self[i] for i in range(self.size)]

    def to_memoryview(self) -> memoryview:
        mv = self._parent.to_memoryview()
        return mv[self._start:self._end]


class BufferPointer:
    """Raw pointer wrapper returned by buffer.ptr inside unsafe blocks."""
    __slots__ = ("_buffer", "_address")

    def __init__(self, buffer: "TypedBuffer") -> None:
        self._buffer = buffer
        self._address = ctypes.addressof(buffer._raw_array)

    @property
    def address(self) -> int:
        return self._address

    def __int__(self) -> int:
        return self._address

    def __index__(self) -> int:
        return self._address

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, BufferPointer):
            return self._address == other._address
        if isinstance(other, int):
            return self._address == other
        return False

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, (BufferPointer, int)):
            return self._address < int(other)
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, (BufferPointer, int)):
            return self._address > int(other)
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, (BufferPointer, int)):
            return self._address <= int(other)
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, (BufferPointer, int)):
            return self._address >= int(other)
        return NotImplemented

    def read_unchecked(self, idx: int) -> Any:
        return self._buffer.read_unchecked(idx)

    def write_unchecked(self, idx: int, val: Any) -> None:
        self._buffer.write_unchecked(idx, val)

    def read(self, dtype: str, idx: int) -> Any:
        c_type = DTYPE_CTYPES.get(dtype, ctypes.c_uint8)
        itemsize = ctypes.sizeof(c_type)
        return c_type.from_address(self._address + idx * itemsize).value

    def write(self, dtype: str, idx: int, val: Any) -> None:
        c_type = DTYPE_CTYPES.get(dtype, ctypes.c_uint8)
        itemsize = ctypes.sizeof(c_type)
        c_type.from_address(self._address + idx * itemsize).value = val

    def __repr__(self) -> str:
        return f"BufferPointer(0x{self._address:x})"


class TypedBuffer:
    """
    First-class typed continuous memory buffer with bounds checking,
    zero-copy slicing, and scoped unchecked pointer access.
    """
    __slots__ = ("dtype_str", "size", "aligned", "c_type", "itemsize", "nbytes", "_raw_array", "_backing_buf")

    def __init__(self, dtype: str, size: int, aligned: int = 0, fill: Any = 0) -> None:
        self.dtype_str = dtype
        self.size = size
        self.aligned = aligned
        self.c_type = DTYPE_CTYPES.get(dtype, ctypes.c_uint8)
        self.itemsize = ctypes.sizeof(self.c_type)
        self.nbytes = self.size * self.itemsize

        if aligned > 1:
            raw_size = self.nbytes + aligned
            self._backing_buf = (ctypes.c_uint8 * raw_size)()
            addr = ctypes.addressof(self._backing_buf)
            offset = (aligned - (addr % aligned)) % aligned
            self._raw_array = (self.c_type * size).from_address(addr + offset)
        else:
            self._backing_buf = None
            self._raw_array = (self.c_type * size)()

        if fill != 0:
            c_val = self.c_type(fill)
            for i in range(size):
                self._raw_array[i] = c_val

    def __len__(self) -> int:
        return self.size

    def __getitem__(self, idx: Any) -> Any:
        if isinstance(idx, (slice, range)):
            start = idx.start or 0
            stop = self.size if idx.stop is None else idx.stop
            if start < 0 or stop > self.size or start > stop:
                raise IndexError(f"Buffer slice [{start}:{stop}] out of bounds for buffer of size {self.size}")
            return BufferSlice(self, start, stop)
        if idx < 0 or idx >= self.size:
            raise IndexError(f"Buffer index {idx} out of bounds for buffer of size {self.size}")
        return self._raw_array[idx]

    def __setitem__(self, idx: int, val: Any) -> None:
        if idx < 0 or idx >= self.size:
            raise IndexError(f"Buffer index {idx} out of bounds for buffer of size {self.size}")
        self._raw_array[idx] = val

    @property
    def ptr(self) -> BufferPointer:
        """Returns a raw pointer wrapper. Only permitted inside an `unsafe:` block."""
        if not _rad_is_unsafe_active():
            raise RuntimeError("Accessing buffer.ptr is only allowed inside an 'unsafe:' block")
        return BufferPointer(self)

    def read_unchecked(self, idx: int) -> Any:
        """Direct memory read without bounds checking. Only permitted inside an `unsafe:` block."""
        if not _rad_is_unsafe_active():
            raise RuntimeError("buffer.read_unchecked() is only allowed inside an 'unsafe:' block")
        return self._raw_array[idx]

    def write_unchecked(self, idx: int, val: Any) -> None:
        """Direct memory write without bounds checking. Only permitted inside an `unsafe:` block."""
        if not _rad_is_unsafe_active():
            raise RuntimeError("buffer.write_unchecked() is only allowed inside an 'unsafe:' block")
        self._raw_array[idx] = self.c_type(val)

    def to_list(self) -> list[Any]:
        return list(self._raw_array)

    def to_bytes(self) -> bytes:
        return bytes(self._raw_array)

    def to_memoryview(self) -> memoryview:
        """Zero-copy memoryview compatible with NumPy and Python buffer protocol."""
        raw_mv = memoryview(self._raw_array).cast("B")
        fmt = DTYPE_FORMAT.get(self.dtype_str, "B")
        if fmt != "B":
            return raw_mv.cast(fmt)
        return raw_mv

    def __buffer__(self, flags: int) -> memoryview:
        return self.to_memoryview()

    def __repr__(self) -> str:
        preview = ", ".join(str(self._raw_array[i]) for i in range(min(4, self.size)))
        if self.size > 4:
            preview += ", ..."
        return f"buffer[{self.dtype_str}](size={self.size}, [{preview}])"


class _BufferFactory:
    """Provides `buffer[u8](size)` and `buffer(size, dtype)` syntax."""
    def __getitem__(self, dtype: Any) -> Callable[..., TypedBuffer]:
        name = getattr(dtype, "__name__", str(dtype))
        def creator(size: int, aligned: int = 0, fill: Any = 0) -> TypedBuffer:
            return TypedBuffer(name, size, aligned=aligned, fill=fill)
        return creator

    def __call__(self, size: int, dtype: str = "u8", aligned: int = 0, fill: Any = 0) -> TypedBuffer:
        return TypedBuffer(dtype, size, aligned=aligned, fill=fill)


buffer = _BufferFactory()


class Arena:
    """
    Contiguous memory arena (bump allocator).
    Enables zero-overhead allocation on a contiguous memory slab
    and O(1) bulk deallocation upon scope exit.
    """
    __slots__ = ("capacity", "used", "_raw_memory", "_is_closed")

    def __init__(self, capacity: int = 1024 * 1024) -> None:
        self.capacity = capacity
        self.used = 0
        self._raw_memory = (ctypes.c_uint8 * capacity)()
        self._is_closed = False

    def alloc(self, size: int, dtype: str = "u8", aligned: int = 8) -> TypedBuffer:
        """Allocates a typed buffer from the arena's memory slab."""
        if self._is_closed:
            raise RuntimeError("Cannot allocate from a closed arena")

        c_type = DTYPE_CTYPES.get(dtype, ctypes.c_uint8)
        itemsize = ctypes.sizeof(c_type)
        total_bytes = size * itemsize

        if aligned > 1:
            remainder = self.used % aligned
            if remainder != 0:
                self.used += (aligned - remainder)

        if self.used + total_bytes > self.capacity:
            raise MemoryError(
                f"Arena out of memory: requested {total_bytes} bytes, "
                f"but only {self.capacity - self.used} remaining (capacity: {self.capacity})"
            )

        ptr_addr = ctypes.addressof(self._raw_memory) + self.used
        self.used += total_bytes

        buf = TypedBuffer(dtype, size, aligned=aligned)
        buf._raw_array = (c_type * size).from_address(ptr_addr)
        return buf

    @property
    def remaining(self) -> int:
        return max(0, self.capacity - self.used)

    def reset(self) -> None:
        """O(1) bulk deallocation of all arena allocations."""
        self.used = 0

    def close(self) -> None:
        self.reset()
        self._is_closed = True

    def __enter__(self) -> "Arena":
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"arena(used={self.used}/{self.capacity} bytes)"


def arena(capacity: int = 1024 * 1024) -> Arena:
    return Arena(capacity=capacity)
