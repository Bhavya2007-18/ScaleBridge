"""Compatibility entry point for the versioned API router.

The implementation lives in :mod:`app.api.router`; the older per-resource
endpoint modules remain in the tree for reference but are no longer mounted.
"""

from app.api.router import router

__all__ = ["router"]
