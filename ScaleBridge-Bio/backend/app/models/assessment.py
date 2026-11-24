"""Compatibility re-export of the canonical SQLAlchemy models.

The canonical definitions live in :mod:`app.db.models`; this module keeps
the historical import path working without defining duplicate tables.
"""

from app.db.models import (
    Assessment,
    CalculationResultRow,
    RiskFlagRow,
    CompatibilityCheckRow,
    ValidationTaskRow,
)

__all__ = ['Assessment', 'CalculationResultRow', 'RiskFlagRow', 'CompatibilityCheckRow', 'ValidationTaskRow']
