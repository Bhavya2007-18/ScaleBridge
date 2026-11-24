"""Compatibility re-export of the canonical SQLAlchemy models.

The canonical definitions live in :mod:`app.db.models`; this module keeps
the historical import path working without defining duplicate tables.
"""

from app.db.models import (
    Vessel,
    VesselVersion,
    VesselParameter,
)

__all__ = ['Vessel', 'VesselVersion', 'VesselParameter']
