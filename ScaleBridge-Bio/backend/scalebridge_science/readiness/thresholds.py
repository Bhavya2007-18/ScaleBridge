"""Versioned, explicitly supplied rule-threshold configuration (docs/12 §3).

No YAML, file reads or environment variables are used here.  The scientific lead
owns the values; every threshold defaults to ``None`` and a rule that depends on
an unset threshold must return ``not_configured``.  A snapshot of this model is
carried in ``ScenarioConfig.thresholds`` and its ``version`` is recorded in the
assessment output.
"""

from __future__ import annotations

from scalebridge_science._pydantic_compat import BaseModel, Field


class DescriptorBand(BaseModel):
    """Allowed target/source ratio band for a non-preserved descriptor."""

    min_ratio: float | None = None
    max_ratio: float | None = None


class SimilarityTolerance(BaseModel):
    """Maximum relative difference between scales for geometric ratios."""

    d_over_t: float | None = None
    hl_over_t: float | None = None


class ThresholdConfig(BaseModel):
    """Expert-configurable rule thresholds (all default to ``None``).

    The canonical keys follow docs/12 §3.  ``d_over_t_rel_tol``,
    ``hl_over_t_rel_tol`` and ``temperature_deviation_max_k`` are retained as
    deprecated flat aliases so that existing snapshots keep their meaning.
    """

    version: str = "0.1.0-unconfigured"
    re_turbulent_min: float | None = None
    descriptor_ratio_band: dict[str, DescriptorBand] = Field(default_factory=dict)
    geometric_similarity_tolerance: SimilarityTolerance = Field(
        default_factory=SimilarityTolerance
    )
    otr_demand_margin: float | None = None
    cooling_margin: float | None = None
    temperature_deviation_max: float | None = None
    do_critical_percent: float | None = None

    # Deprecated aliases (kept for backwards-compatible snapshots).
    d_over_t_rel_tol: float | None = None
    hl_over_t_rel_tol: float | None = None
    temperature_deviation_max_k: float | None = None


__all__ = ["DescriptorBand", "SimilarityTolerance", "ThresholdConfig"]
