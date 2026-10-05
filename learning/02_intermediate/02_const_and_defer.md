# Lesson 05: Variables (`const` / `let`) & Cleanup (`defer` / `using`)

## 1. The Problem in Python: Accidental Reassignments & Complex Cleanup

In standard Python, all variables are globally mutable by default, leading to accidental state mutation:
```python
# Standard Python: Silent bug introduced by accidental mutation
MAX_CONNECTIONS = 100
MAX_CONNECTIONS = 200 # Allowed without warning!
```
Furthermore, resource cleanup requires multiple nested `with` blocks or `try...finally` stacks that increase indentation.

---

## 2. 3-Way Code Comparison

### Radical Source (`.rad`)
```radical
# 1. Compile-time constant invariant
const MAX_CONNECTIONS = 100
let active_connections = 0

active_connections += 1 # Allowed!
# MAX_CONNECTIONS = 200 # RadicalCompileError: Constant 'MAX_CONNECTIONS' cannot be reassigned!

# 2. Scoped deterministic resource block
using log = open("server.log", "a"):
    log.write("Request handled\n")

# 3. LIFO cleanup stack for functions
def sync_databases():
    lock = acquire_cluster_lock()
    defer lock.release() # Runs 2nd (LIFO)

    conn = db.connect()
    defer conn.close()   # Runs 1st (LIFO)

    conn.execute("SYNC")
```

### Equivalent Standard Python
```python
# Convention only (no compiler guarantee)
MAX_CONNECTIONS = 100
active_connections = 0
active_connections += 1

with open("server.log", "a") as log:
    log.write("Request handled\n")

def sync_databases():
    lock = acquire_cluster_lock()
    try:
        conn = db.connect()
        try:
            conn.execute("SYNC")
        finally:
            conn.close()
    finally:
        lock.release()
```

### Transpiled Python Output (`radical build`)
```python
from radical.runtime import _RadicalDeferStack

MAX_CONNECTIONS = 100
active_connections = 0
active_connections += 1

with open("server.log", "a") as log:
    log.write("Request handled\n")

def sync_databases():
    with _RadicalDeferStack() as _rad_defer:
        lock = acquire_cluster_lock()
        _rad_defer.defer(lambda: lock.release())

        conn = db.connect()
        _rad_defer.defer(lambda: conn.close())

        conn.execute("SYNC")
```

---

## 3. Why `defer` is Superior to Deep `try...finally`

1. **Immediate Proximity**: The cleanup logic (`defer file.close()`) is placed right beside the initialization (`file = open(...)`), making missing cleanups obvious during code review.
2. **Deterministic LIFO Order**: Defers execute in Last-In First-Out order, guaranteeing dependencies (locks, sockets, file handles) are released in the exact reverse order of acquisition.
3. **Exception Safety**: If any exception is raised, all registered defer callbacks are guaranteed to execute as the stack unwinds.
