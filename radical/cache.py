"""
Bytecode and AST caching for Radical.
Employs SHA-256 content hashes and Python version metadata.
"""

import os
import sys
import hashlib
import marshal
from typing import Optional, Any


def get_cache_dir(filepath: str) -> str:
    """Computes the __radcache__ directory adjacent to the source file."""
    abs_path = os.path.abspath(filepath)
    return os.path.join(os.path.dirname(abs_path) or ".", "__radcache__")


def get_cache_path(filepath: str) -> str:
    """Computes the .pyc path in the cache directory."""
    abs_path = os.path.abspath(filepath)
    cache_dir = get_cache_dir(abs_path)
    base_name = os.path.basename(abs_path)
    return os.path.join(cache_dir, f"{base_name}.pyc")


def compute_content_hash(source: str, version: str) -> str:
    """Generates a unique SHA-256 hash across source content, Python runtime, and Radical version."""
    return hashlib.sha256(
        source.encode("utf-8") + sys.version.encode("utf-8") + version.encode("utf-8")
    ).hexdigest()


def load_cached_code(filepath: str, content_hash: str, version: str) -> Optional[Any]:
    """Loads compiled code object from cache if content hash and version match."""
    cache_file = get_cache_path(filepath)
    if not os.path.exists(cache_file):
        return None

    try:
        abs_path = os.path.abspath(filepath)
        mtime = os.path.getmtime(abs_path)
        with open(cache_file, "rb") as cf:
            cached_key = marshal.load(cf)
            cached_ver = marshal.load(cf)
            if (cached_key == content_hash or cached_key == mtime) and cached_ver == version:
                return marshal.load(cf)
    except Exception:
        return None

    return None


def save_cached_code(filepath: str, content_hash: str, version: str, compiled: Any) -> None:
    """Serializes compiled code object to disk cache."""
    try:
        cache_dir = get_cache_dir(filepath)
        cache_file = get_cache_path(filepath)
        os.makedirs(cache_dir, exist_ok=True)
        with open(cache_file, "wb") as cf:
            marshal.dump(content_hash, cf)
            marshal.dump(version, cf)
            marshal.dump(compiled, cf)
    except Exception:
        pass
