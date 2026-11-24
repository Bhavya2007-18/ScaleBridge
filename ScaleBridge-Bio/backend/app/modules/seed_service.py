"""Compatibility wrapper for the canonical demo seed implementation.

The full seed routine now lives in :mod:`app.seed.demo_data`.
"""

from __future__ import annotations

from app.seed.demo_data import (  # noqa: F401
    generate_synthetic_batch_csv,
    seed_demo_data,
    seed_demo_workspace,
)

__all__ = [
    "generate_synthetic_batch_csv",
    "seed_demo_data",
    "seed_demo_workspace",
]
