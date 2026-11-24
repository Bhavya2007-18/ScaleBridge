"""Small pydantic compatibility shim.

The scientific package uses pydantic for its contracts.  In constrained
execution environments where the compiled pydantic core cannot be loaded, the
same minimal surface (``BaseModel`` / ``Field``) is provided by a dataclass
fallback so that the pure-Python engine remains importable.  This module is
private to the package.
"""

from __future__ import annotations

from typing import Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    import dataclasses
    from collections.abc import Callable

    def Field(  # type: ignore[misc]
        *,
        default: Any = ...,
        default_factory: Callable[[], Any] | None = None,
        **kwargs: Any,
    ) -> Any:
        if default_factory is not None:
            return dataclasses.field(default_factory=default_factory)
        if default is not ...:
            return dataclasses.field(default=default)
        return dataclasses.field()

    class BaseModel:  # type: ignore[no-redef]
        def __init__(self, **kwargs: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in kwargs:
                    setattr(self, name, kwargs[name])
                elif hasattr(self.__class__, name):
                    default_val = getattr(self.__class__, name)
                    if (
                        isinstance(default_val, dataclasses.Field)
                        and default_val.default_factory is not dataclasses.MISSING
                    ):
                        setattr(self, name, default_val.default_factory())
                    elif (
                        isinstance(default_val, dataclasses.Field)
                        and default_val.default is not dataclasses.MISSING
                    ):
                        setattr(self, name, default_val.default)
                    elif not isinstance(default_val, dataclasses.Field):
                        setattr(self, name, default_val)
                else:
                    setattr(self, name, None)
            for k, v in kwargs.items():
                if k not in annotations:
                    setattr(self, k, v)

        def model_dump(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
            def _to_dict(obj: Any) -> Any:
                if isinstance(obj, BaseModel):
                    return obj.model_dump()
                if isinstance(obj, list):
                    return [_to_dict(i) for i in obj]
                if isinstance(obj, dict):
                    return {k: _to_dict(v) for k, v in obj.items()}
                return obj

            res: dict[str, Any] = {}
            for k in getattr(self.__class__, "__annotations__", {}):
                if hasattr(self, k):
                    res[k] = _to_dict(getattr(self, k))
            return res

        def __repr__(self) -> str:
            fields = ", ".join(
                f"{k}={getattr(self, k)!r}"
                for k in getattr(self.__class__, "__annotations__", {})
                if hasattr(self, k)
            )
            return f"{self.__class__.__name__}({fields})"

        def __eq__(self, other: object) -> bool:
            if not isinstance(other, self.__class__):
                return False
            return self.model_dump() == other.model_dump()


__all__ = ["BaseModel", "Field"]
