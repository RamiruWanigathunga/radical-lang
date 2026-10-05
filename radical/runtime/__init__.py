"""
Radical Language Unified Runtime Subsystem.
Modularized runtime package re-exporting all primitives for 100% backward compatibility.
"""

from radical.runtime.safety import (
    _rad_safe_attr,
    _rad_safe_item,
    _rad_safe_call,
    _rad_coalesce,
)
from radical.runtime.defer import _RadicalDeferStack
from radical.runtime.parallel import _rad_parallel_for
from radical.runtime.simd import SIMDVector, _SIMDFactory, simd
from radical.gpu import gpu, GPUBuffer
from radical.runtime.adt import (
    Result,
    Ok,
    Err,
    Option,
    Some,
    Nil,
    None_,
)
from radical.runtime.channels import (
    Channel,
    _ChanFactory,
    chan,
    select,
)
from radical.runtime.unsafe import (
    _RadicalUnsafeContext,
    _rad_unsafe_context,
    _rad_is_unsafe_active,
)
from radical.runtime.memory import (
    u8, uint8, byte,
    i8, int8,
    u16, uint16, i16, int16,
    u32, uint32, i32, int32,
    u64, uint64, i64, int64,
    f16, f32, float32, f64, float64,
    DTYPE_CTYPES,
    DTYPE_FORMAT,
    BufferSlice,
    BufferPointer,
    TypedBuffer,
    _BufferFactory,
    buffer,
    Arena,
    arena,
)
from radical.runtime.structs import _rad_copy_with
from radical.runtime.native import _rad_native

__all__ = [
    # Safety & Coalescing
    "_rad_safe_attr",
    "_rad_safe_item",
    "_rad_safe_call",
    "_rad_coalesce",
    # Defer
    "_RadicalDeferStack",
    # Parallel
    "_rad_parallel_for",
    # SIMD & GPU
    "SIMDVector",
    "_SIMDFactory",
    "simd",
    "gpu",
    "GPUBuffer",
    # ADT
    "Result",
    "Ok",
    "Err",
    "Option",
    "Some",
    "Nil",
    "None_",
    # Channels & Select
    "Channel",
    "_ChanFactory",
    "chan",
    "select",
    # Unsafe
    "_RadicalUnsafeContext",
    "_rad_unsafe_context",
    "_rad_is_unsafe_active",
    # Memory & Buffers
    "u8", "uint8", "byte",
    "i8", "int8",
    "u16", "uint16", "i16", "int16",
    "u32", "uint32", "i32", "int32",
    "u64", "uint64", "i64", "int64",
    "f16", "f32", "float32", "f64", "float64",
    "DTYPE_CTYPES",
    "DTYPE_FORMAT",
    "BufferSlice",
    "BufferPointer",
    "TypedBuffer",
    "_BufferFactory",
    "buffer",
    "Arena",
    "arena",
    # Structs & Native
    "_rad_copy_with",
    "_rad_native",
]
