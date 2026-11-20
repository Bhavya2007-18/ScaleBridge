"""Seed service wrapper around the canonical demo-data routine."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.seed.demo_data import seed_demo_data


def run_seed(db: Session) -> dict:
    """Seed the synthetic demonstration workspace (idempotent)."""
    return seed_demo_data(db)


__all__ = ["run_seed", "seed_demo_data"]
