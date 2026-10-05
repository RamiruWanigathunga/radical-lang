import pytest
from radical.runtime import simd, SIMDVector


def test_simd_initialization_and_indexing():
    v = simd[float, 4](1.0, 2.0, 3.0, 4.0)
    assert len(v) == 4
    assert v[0] == 1.0
    assert v[3] == 4.0
    assert v.to_list() == [1.0, 2.0, 3.0, 4.0]


def test_simd_scalar_broadcast():
    v = simd[float, 4](5.0)
    assert v.to_list() == [5.0, 5.0, 5.0, 5.0]


def test_simd_vector_arithmetic():
    v1 = simd[float, 4](1.0, 2.0, 3.0, 4.0)
    v2 = simd[float, 4](10.0, 20.0, 30.0, 40.0)

    # Addition
    v_add = v1 + v2
    assert v_add.to_list() == [11.0, 22.0, 33.0, 44.0]

    # Subtraction
    v_sub = v2 - v1
    assert v_sub.to_list() == [9.0, 18.0, 27.0, 36.0]

    # Multiplication
    v_mul = v1 * v2
    assert v_mul.to_list() == [10.0, 40.0, 90.0, 160.0]

    # Division
    v_div = v2 / 10.0
    assert v_div.to_list() == [1.0, 2.0, 3.0, 4.0]


def test_simd_dot_product_and_sum():
    v1 = simd[int, 3](1, 2, 3)
    v2 = simd[int, 3](4, 5, 6)

    assert v1.dot(v2) == (1*4 + 2*5 + 3*6)  # 4 + 10 + 18 = 32
    assert v1.sum() == 6
