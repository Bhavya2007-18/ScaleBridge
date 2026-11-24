"""Scale-up criterion metadata (docs/11 §8)."""

from __future__ import annotations

from scalebridge_science._pydantic_compat import BaseModel


class CriterionMetadata(BaseModel):
    criterion_id: str
    name: str
    kind: str  # "agitation" | "aeration" | "evaluation"
    equation_text: str
    description: str


CRITERIA_REGISTRY: dict[str, CriterionMetadata] = {
    "S-PV": CriterionMetadata(
        criterion_id="S-PV",
        name="Constant Power per Volume (P/V)",
        kind="agitation",
        equation_text="N_t = [ (P/V)_s · V_t / (n_imp,t · N_p,t · ρ · D_t⁵) ]^(1/3)",
        description="Solves for target agitation speed N_t that preserves source power per working volume.",
    ),
    "S-TIP": CriterionMetadata(
        criterion_id="S-TIP",
        name="Constant Impeller Tip Speed (u_tip)",
        kind="agitation",
        equation_text="N_t = N_s · (D_s / D_t)",
        description="Solves for target agitation speed N_t that preserves impeller peripheral speed.",
    ),
    "S-VVM": CriterionMetadata(
        criterion_id="S-VVM",
        name="Constant Gas Flow per Volume (vvm)",
        kind="aeration",
        equation_text="Q_g,t = vvm_s · V_t",
        description="Solves for target gas flow rate Q_g,t that preserves volumetric aeration per liquid volume.",
    ),
    "S-VS": CriterionMetadata(
        criterion_id="S-VS",
        name="Constant Superficial Gas Velocity (v_s)",
        kind="aeration",
        equation_text="Q_g,t = v_s,s · (π · T_t² / 4)",
        description="Solves for target gas flow rate Q_g,t that preserves superficial gas velocity.",
    ),
    "S-KLA": CriterionMetadata(
        criterion_id="S-KLA",
        name="kLa / Oxygen Transfer Evidence Comparison",
        kind="evaluation",
        equation_text="Compare documented target kLa & OTR against source kLa & oxygen demand",
        description="Evaluates documented kLa evidence without extrapolating unvalidated kLa correlations.",
    ),
}


__all__ = ["CRITERIA_REGISTRY", "CriterionMetadata"]
