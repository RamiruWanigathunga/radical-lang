"""
Radical Language Runtime: Struct Copy-Update.
Implements immutable functional copy-with updates for dataclasses and objects.
"""

import copy
import dataclasses
from typing import Any


def _rad_copy_with(obj: Any, **kwargs: Any) -> Any:
    """
    Immutable/functional copy-update: `p with { x: 10 }`.
    """
    if dataclasses.is_dataclass(obj):
        return dataclasses.replace(obj, **kwargs)
    if isinstance(obj, dict):
        res = dict(obj)
        res.update(kwargs)
        return res
    res = copy.copy(obj)
    for k, v in kwargs.items():
        setattr(res, k, v)
    return res
