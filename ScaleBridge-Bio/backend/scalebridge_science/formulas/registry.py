"""Formula registry metadata and shared execution policy (docs/10 §5, docs/11).

The registry is deliberately data-only.  Formula implementations live in
``oxygen.py``, ``hydrodynamics.py`` and ``aeration.py`` and call
``run_formula`` below so that review status, missing-input handling and
non-finite/division-by-zero handling are applied consistently.
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import Literal

from scalebridge_science._pydantic_compat import BaseModel
from scalebridge_science.contracts import CalculationResult, Provenance, Quantity, ValueNature
from scalebridge_science.evidence import derive_evidence_level
from scalebridge_science.units import convert_value

FORMULA_REGISTRY_VERSION = "0.1.0"


class FormulaMetadata(BaseModel):
    """Everything the UI and report need to render a formula (docs/10 §5)."""

    formula_id: str
    version: str
    name: str
    equation_text: str
    equation_latex: str
    variables: dict[str, str]
    output: str
    source_basis: str
    blueprint_status: Literal["confirmed", "proposed"]
    review_status: Literal["draft", "pending_review", "approved", "deprecated"]
    assumptions: list[str]
    validity_limits: list[str]
    required_inputs: list[str]
    output_unit_si: str
    display_unit: str


FORMULA_REGISTRY: dict[str, FormulaMetadata] = {
    "F-TIP-001": FormulaMetadata(
        formula_id="F-TIP-001",
        name="Impeller tip speed",
        version="1.0.0",
        equation_text="u_tip = π · N · D",
        equation_latex=r"u_{tip} = \pi N D",
        variables={"N": "Impeller rotational speed [1/s]", "D": "Impeller diameter [m]"},
        output="u_tip [m/s]",
        output_unit_si="meter / second",
        display_unit="m/s",
        blueprint_status="confirmed",
        review_status="approved",
        source_basis="ScaleBridge Bio Startup Blueprint p.6",
        assumptions=[
            "Evaluated using characteristic impeller diameter D and rotational speed N (in rev/s)."
        ],
        validity_limits=[
            "Describes peripheral impeller speed only; local shear rates also depend on impeller blade geometry."
        ],
        required_inputs=["N", "D"],
    ),
    "F-RE-001": FormulaMetadata(
        formula_id="F-RE-001",
        name="Impeller Reynolds number",
        version="1.0.0",
        equation_text="Re = ρ · N · D² / μ",
        equation_latex=r"Re = \frac{\rho N D^2}{\mu}",
        variables={
            "rho": "Broth density [kg/m³]",
            "N": "Impeller rotational speed [1/s]",
            "D": "Impeller diameter [m]",
            "mu": "Broth dynamic viscosity [Pa·s]",
        },
        output="Re [dimensionless]",
        output_unit_si="dimensionless",
        display_unit="dimensionless",
        blueprint_status="confirmed",
        review_status="approved",
        source_basis="ScaleBridge Bio Startup Blueprint p.6",
        assumptions=[
            "Assumes Newtonian liquid behavior with dynamic viscosity μ at process temperature."
        ],
        validity_limits=[
            "Non-Newtonian or high-viscosity mycelial/polymeric broths require apparent viscosity characterization."
        ],
        required_inputs=["rho", "N", "D", "mu"],
    ),
    "F-PV-001": FormulaMetadata(
        formula_id="F-PV-001",
        name="Power per liquid working volume",
        version="1.0.0",
        equation_text="P/V = P / V_w",
        equation_latex=r"P/V = \frac{P}{V_w}",
        variables={"P": "Power input to liquid [W]", "V_w": "Liquid working volume [m³]"},
        output="P/V [W/m³]",
        output_unit_si="watt / m**3",
        display_unit="W/m^3",
        blueprint_status="confirmed",
        review_status="approved",
        source_basis="ScaleBridge Bio Startup Blueprint p.6",
        assumptions=[
            "Volume-averaged power dissipation; local energy dissipation near the impeller is significantly higher."
        ],
        validity_limits=["Requires either measured shaft power P or an ungassed power estimate P₀."],
        required_inputs=["P", "V_w"],
    ),
    "F-PWR-001": FormulaMetadata(
        formula_id="F-PWR-001",
        name="Ungassed agitation power from power number",
        version="1.0.0",
        equation_text="P₀ = n_imp · N_p · ρ · N³ · D⁵",
        equation_latex=r"P_0 = n_{imp} N_p \rho N^3 D^5",
        variables={
            "N_p": "Impeller ungassed power number [dimensionless]",
            "rho": "Broth density [kg/m³]",
            "N": "Impeller rotational speed [1/s]",
            "D": "Impeller diameter [m]",
            "n_imp": "Impeller count [dimensionless]",
        },
        output="P₀ [W]",
        output_unit_si="watt",
        display_unit="W",
        blueprint_status="proposed",
        review_status="pending_review",
        source_basis="Proposed engineering correlation (OQ-012); requires bioprocess advisor sign-off",
        assumptions=[
            "Constant turbulent power number N_p for baffled vessel.",
            "Ungassed power estimate; aeration typically reduces actual gassed power draw.",
            "Multiple impellers treated as additive without hydrodynamic interaction.",
        ],
        validity_limits=["Valid only in fully turbulent flow regime for the specified impeller geometry."],
        required_inputs=["N_p", "rho", "N", "D"],
    ),
    "F-VVM-001": FormulaMetadata(
        formula_id="F-VVM-001",
        name="Gas flow per liquid working volume (vvm)",
        version="1.0.0",
        equation_text="vvm = Q_g / V_w",
        equation_latex=r"vvm = \frac{Q_g}{V_w}",
        variables={"Q_g": "Volumetric gas flow rate [m³/s]", "V_w": "Liquid working volume [m³]"},
        output="vvm [1/min]",
        output_unit_si="1 / second",
        display_unit="vvm",
        blueprint_status="confirmed",
        review_status="approved",
        source_basis="ScaleBridge Bio Startup Blueprint p.6",
        assumptions=["Gas flow rate Q_g evaluated at consistent reference conditions."],
        validity_limits=["Does not account for gas compressibility across tall liquid columns."],
        required_inputs=["Q_g", "V_w"],
    ),
    "F-VS-001": FormulaMetadata(
        formula_id="F-VS-001",
        name="Superficial gas velocity",
        version="1.0.0",
        equation_text="v_s = Q_g / (π · T² / 4)",
        equation_latex=r"v_s = \frac{Q_g}{\pi T^2 / 4}",
        variables={"Q_g": "Volumetric gas flow rate [m³/s]", "T": "Vessel inner diameter [m]"},
        output="v_s [m/s]",
        output_unit_si="meter / second",
        display_unit="m/s",
        blueprint_status="proposed",
        review_status="pending_review",
        source_basis="ScaleBridge Bio Startup Blueprint p.5 ('gas flow descriptors')",
        assumptions=["Uniform cylindrical vessel cross-section A = π·T²/4."],
        validity_limits=["High superficial gas velocity can induce impeller flooding or excessive foaming."],
        required_inputs=["Q_g", "T"],
    ),
    "F-DOC-001": FormulaMetadata(
        formula_id="F-DOC-001",
        name="Dissolved oxygen concentration from % air saturation",
        version="1.0.0",
        equation_text="C_L = (DO_% / 100) · C*",
        equation_latex=r"C_L = \frac{DO_{\%}}{100} C^*",
        variables={
            "DO": "Dissolved oxygen [% air saturation]",
            "C_star": "Oxygen saturation concentration C* [mol/m³]",
        },
        output="C_L [mol/m³]",
        output_unit_si="mol / m**3",
        display_unit="mmol/L",
        blueprint_status="proposed",
        review_status="pending_review",
        source_basis="Proposed auxiliary conversion for OTR = kLa(C* - C_L) (Blueprint p.6)",
        assumptions=["DO probe calibrated to 100% air saturation at conditions matching C*."],
        validity_limits=["Requires process-relevant C* accounting for temperature, pressure, and medium salinity."],
        required_inputs=["DO", "C_star"],
    ),
    "F-OTR-001": FormulaMetadata(
        formula_id="F-OTR-001",
        name="Oxygen transfer rate (OTR) at operating DO",
        version="1.0.0",
        equation_text="OTR = kLa · (C* − C_L)",
        equation_latex=r"\mathrm{OTR} = k_La (C^* - C_L)",
        variables={
            "kLa": "Volumetric oxygen mass-transfer coefficient [1/s]",
            "C_star": "Oxygen saturation concentration C* [mol/m³]",
            "C_L": "Operating dissolved oxygen concentration C_L [mol/m³]",
        },
        output="OTR [mol/(m³·s)]",
        output_unit_si="mol / (m**3 * second)",
        display_unit="mmol/(L*h)",
        blueprint_status="confirmed",
        review_status="approved",
        source_basis="ScaleBridge Bio Startup Blueprint p.6",
        assumptions=[
            "Well-mixed liquid phase with uniform C_L and C*.",
            "kLa measured or validated for the actual vessel, sparger, medium, and operating point.",
        ],
        validity_limits=[
            "OTR = kLa(C* - C_L) is a relationship, not a complete prediction model (Blueprint p.6)."
        ],
        required_inputs=["kLa", "C_star", "C_L"],
    ),
    "F-OTR-MAX": FormulaMetadata(
        formula_id="F-OTR-MAX",
        name="Theoretical maximum OTR driving bound (at C_L = 0)",
        version="1.0.0",
        equation_text="OTR_max = kLa · C*",
        equation_latex=r"\mathrm{OTR}_{max} = k_La C^*",
        variables={
            "kLa": "Volumetric oxygen mass-transfer coefficient [1/s]",
            "C_star": "Oxygen saturation concentration C* [mol/m³]",
        },
        output="OTR_max [mol/(m³·s)]",
        output_unit_si="mol / (m**3 * second)",
        display_unit="mmol/(L*h)",
        blueprint_status="confirmed",
        review_status="approved",
        source_basis="ScaleBridge Bio Startup Blueprint p.6 (special case C_L = 0)",
        assumptions=[
            "Theoretical upper bound at zero dissolved oxygen (C_L = 0); not a viable aerobic operating point."
        ],
        validity_limits=["Upper bound only; aerobic organisms require C_L above critical DO."],
        required_inputs=["kLa", "C_star"],
    ),
    "F-GEO-001": FormulaMetadata(
        formula_id="F-GEO-001",
        name="Impeller-to-tank diameter ratio (D/T)",
        version="1.0.0",
        equation_text="D/T = D / T",
        equation_latex=r"D/T = \frac{D}{T}",
        variables={"D": "Impeller diameter [m]", "T": "Vessel inner diameter [m]"},
        output="D/T [dimensionless]",
        output_unit_si="dimensionless",
        display_unit="dimensionless",
        blueprint_status="proposed",
        review_status="approved",
        source_basis="Geometric similarity descriptor (Blueprint p.3, p.11)",
        assumptions=["Characteristic impeller diameter D relative to inner tank diameter T."],
        validity_limits=["Does not capture baffle geometry or impeller clearance."],
        required_inputs=["D", "T"],
    ),
    "F-GEO-002": FormulaMetadata(
        formula_id="F-GEO-002",
        name="Liquid aspect ratio (H_L/T)",
        version="1.0.0",
        equation_text="H_L/T = H_L / T",
        equation_latex=r"H_L/T = \frac{H_L}{T}",
        variables={"H_L": "Liquid height at working volume [m]", "T": "Vessel inner diameter [m]"},
        output="H_L/T [dimensionless]",
        output_unit_si="dimensionless",
        display_unit="dimensionless",
        blueprint_status="proposed",
        review_status="approved",
        source_basis="Geometric similarity descriptor (Blueprint p.3, p.11)",
        assumptions=["Liquid height H_L at nominal working volume."],
        validity_limits=["Varies during fed-batch volume expansion."],
        required_inputs=["H_L", "T"],
    ),
}


def _make_missing_result(
    meta: FormulaMetadata,
    scale: Literal["source", "target"],
    criterion_id: str | None,
    present_inputs: dict[str, Quantity],
    missing_inputs: list[str],
) -> CalculationResult:
    return CalculationResult(
        formula_id=meta.formula_id,
        formula_name=meta.name,
        formula_version=meta.version,
        review_status=meta.review_status,
        scale=scale,
        criterion_id=criterion_id,
        equation=meta.equation_text,
        inputs=present_inputs,
        output=None,
        status="insufficient_evidence",
        missing_inputs=missing_inputs,
        evidence_level="insufficient",
        assumptions=list(meta.assumptions),
        warnings=[],
    )


def _make_error_result(
    meta: FormulaMetadata,
    scale: Literal["source", "target"],
    criterion_id: str | None,
    inputs: dict[str, Quantity],
    message: str,
) -> CalculationResult:
    return CalculationResult(
        formula_id=meta.formula_id,
        formula_name=meta.name,
        formula_version=meta.version,
        review_status=meta.review_status,
        scale=scale,
        criterion_id=criterion_id,
        equation=meta.equation_text,
        inputs=inputs,
        output=None,
        status="error",
        missing_inputs=[],
        evidence_level="insufficient",
        assumptions=list(meta.assumptions),
        warnings=[message],
    )


def _make_not_applicable_result(
    meta: FormulaMetadata,
    scale: Literal["source", "target"],
    criterion_id: str | None,
    inputs: dict[str, Quantity],
) -> CalculationResult:
    return CalculationResult(
        formula_id=meta.formula_id,
        formula_name=meta.name,
        formula_version=meta.version,
        review_status=meta.review_status,
        scale=scale,
        criterion_id=criterion_id,
        equation=meta.equation_text,
        inputs=inputs,
        output=None,
        status="not_applicable",
        missing_inputs=[],
        evidence_level="insufficient",
        assumptions=list(meta.assumptions),
        warnings=[
            f"FORMULA_DRAFT_NOT_EXECUTED: {meta.formula_id} has review_status 'draft' and is never executed in assessments."
        ],
    )


def _make_computed_result(
    meta: FormulaMetadata,
    scale: Literal["source", "target"],
    criterion_id: str | None,
    inputs: dict[str, Quantity],
    value_si: float,
    extra_assumptions: list[str] | None = None,
    extra_warnings: list[str] | None = None,
) -> CalculationResult:
    display_val = (
        value_si
        if meta.output_unit_si == meta.display_unit
        else convert_value(value_si, meta.output_unit_si, meta.display_unit)
    )
    ev_level = derive_evidence_level(inputs.values())
    warnings = list(extra_warnings or [])
    if meta.review_status == "pending_review":
        warnings.append(
            f"FORMULA_PENDING_REVIEW: {meta.formula_id} is pending formal domain-expert review."
        )

    out_qty = Quantity(
        value=value_si,
        unit=meta.output_unit_si,
        original_value=display_val,
        original_unit=meta.display_unit,
        display_value=display_val,
        display_unit=meta.display_unit,
        provenance=Provenance.calculated,
        value_nature=ValueNature.calculated,
        source_ref=f"{meta.formula_id}@{meta.version}",
    )

    return CalculationResult(
        formula_id=meta.formula_id,
        formula_name=meta.name,
        formula_version=meta.version,
        review_status=meta.review_status,
        scale=scale,
        criterion_id=criterion_id,
        equation=meta.equation_text,
        inputs=inputs,
        output=out_qty,
        status="computed",
        missing_inputs=[],
        evidence_level=ev_level,
        assumptions=list(meta.assumptions) + list(extra_assumptions or []),
        warnings=warnings,
    )


def run_formula(
    meta: FormulaMetadata,
    scale: Literal["source", "target"],
    criterion_id: str | None,
    inputs: dict[str, Quantity],
    missing_inputs: list[str],
    compute: Callable[[], float],
    extra_assumptions: list[str] | None = None,
    extra_warnings: list[str] | None = None,
) -> CalculationResult:
    """Apply the shared formula execution policy and build a result.

    - ``draft`` formulas are never executed.
    - any missing required input yields ``insufficient_evidence`` (no defaults).
    - division by zero / non-finite results yield ``error`` for this calculation only.
    - ``pending_review`` results carry ``FORMULA_PENDING_REVIEW``.
    """
    if meta.review_status == "draft":
        return _make_not_applicable_result(meta, scale, criterion_id, inputs)
    if missing_inputs:
        return _make_missing_result(meta, scale, criterion_id, inputs, missing_inputs)
    try:
        value_si = compute()
    except ZeroDivisionError:
        return _make_error_result(
            meta,
            scale,
            criterion_id,
            inputs,
            "Division by zero encountered while evaluating formula.",
        )
    except (OverflowError, ValueError) as exc:
        return _make_error_result(
            meta,
            scale,
            criterion_id,
            inputs,
            f"Non-finite numerical result encountered: {exc}",
        )
    if not math.isfinite(value_si):
        return _make_error_result(
            meta,
            scale,
            criterion_id,
            inputs,
            "Non-finite numerical result encountered.",
        )
    return _make_computed_result(
        meta,
        scale,
        criterion_id,
        inputs,
        value_si,
        extra_assumptions=extra_assumptions,
        extra_warnings=extra_warnings,
    )


__all__ = [
    "FORMULA_REGISTRY",
    "FORMULA_REGISTRY_VERSION",
    "FormulaMetadata",
    "run_formula",
]
