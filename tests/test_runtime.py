import pytest
from radical.runtime import (
    _rad_safe_attr,
    _rad_safe_item,
    _rad_safe_call,
    _rad_coalesce,
    _RadicalDeferStack,
)


def test_safe_attr():
    class User:
        def __init__(self, name):
            self.name = name

    u = User("Alice")
    assert _rad_safe_attr(u, "name") == "Alice"
    assert _rad_safe_attr(u, "non_existent") is None
    assert _rad_safe_attr(None, "name") is None


def test_safe_item():
    # List indexing
    lst = [10, 20, 30]
    assert _rad_safe_item(lst, 0) == 10
    assert _rad_safe_item(lst, 5) is None
    assert _rad_safe_item(None, 0) is None

    # Dict lookup
    d = {"key": "value"}
    assert _rad_safe_item(d, "key") == "value"
    assert _rad_safe_item(d, "missing") is None
    assert _rad_safe_item(None, "key") is None


def test_safe_call():
    def greet(who):
        return f"Hello, {who}!"

    assert _rad_safe_call(greet, "World") == "Hello, World!"
    assert _rad_safe_call(None, "World") is None
    assert _rad_safe_call(42, "World") is None


def test_coalesce():
    # Only None triggers fallback; falsy values are preserved
    assert _rad_coalesce(None, "default") == "default"
    assert _rad_coalesce(0, 10) == 0
    assert _rad_coalesce(False, True) is False
    assert _rad_coalesce("", "empty") == ""
    assert _rad_coalesce("val", "default") == "val"

    # Callable fallback
    calls = []
    def lazy_fallback():
        calls.append(1)
        return "lazy"

    assert _rad_coalesce("present", lazy_fallback) == "present"
    assert len(calls) == 0
    assert _rad_coalesce(None, lazy_fallback) == "lazy"
    assert len(calls) == 1


def test_defer_stack_lifo():
    log = []

    def task1():
        log.append(1)

    def task2():
        log.append(2)

    def task3():
        log.append(3)

    with _RadicalDeferStack() as stack:
        stack.defer(task1)
        stack.defer(task2)
        stack.defer(task3)
        log.append("body")

    assert log == ["body", 3, 2, 1]
