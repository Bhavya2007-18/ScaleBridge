"""Reference input builder shared by regression tests."""

from __future__ import annotations

from scalebridge_science.contracts import (
    AssessmentInput,
    CriterionSelection,
    KlaEvidencePoint,
    MediumProperties,
    ProcessSummary,
    ScenarioConfig,
    ThresholdConfig,
    VesselSpec,
)
from scalebridge_science.units import to_si_quantity


def build_reference_input() -> AssessmentInput:
    src_vessel = VesselSpec(
        vessel_version_id="v-src-1",
        name="Lab-2L",
        scale_class="lab",
        impeller_type="rushton_turbine",
        impeller_count=1,
        sparger_type="ring",
        instrumentation=["ph_probe", "do_probe", "temperature_probe"],
        controls=["ph_control", "temperature_control", "do_cascade_agitation"],
        parameters={
            "working_volume_min": to_si_quantity(0.8, "L", "working_volume_min", "vendor_datasheet"),
            "working_volume_max": to_si_quantity(2.0, "L", "working_volume_max", "vendor_datasheet"),
            "vessel_inner_diameter": to_si_quantity(0.13, "m", "vessel_inner_diameter", "vendor_datasheet"),
            "liquid_height_at_working_volume": to_si_quantity(0.15, "m", "liquid_height_at_working_volume", "manual_entry"),
            "impeller_diameter": to_si_quantity(0.055, "m", "impeller_diameter", "vendor_datasheet"),
            "impeller_power_number": to_si_quantity(5.0, "dimensionless", "impeller_power_number", "vendor_datasheet"),
            "agitation_speed_min": to_si_quantity(100.0, "rpm", "agitation_speed_min", "vendor_datasheet"),
            "agitation_speed_max": to_si_quantity(1200.0, "rpm", "agitation_speed_max", "vendor_datasheet"),
        },
        kla_evidence=[
            KlaEvidencePoint(
                id="kla-src-1",
                kla=to_si_quantity(120.0, "1/h", "kla", "lab_assay"),
                agitation_speed=to_si_quantity(500.0, "rpm", "agitation_speed", "lab_assay"),
                gas_flow=to_si_quantity(1.0, "L/min", "airflow", "lab_assay"),
                working_volume=to_si_quantity(2.0, "L", "working_volume", "lab_assay"),
                medium_description="Defined medium",
            )
        ],
    )

    tgt_vessel = VesselSpec(
        vessel_version_id="v-tgt-1",
        name="Pilot-200L",
        scale_class="pilot",
        impeller_type="rushton_turbine",
        impeller_count=1,
        sparger_type="ring",
        instrumentation=["ph_probe", "do_probe", "temperature_probe"],
        controls=["ph_control", "temperature_control"],
        parameters={
            "working_volume_min": to_si_quantity(60.0, "L", "working_volume_min", "vendor_datasheet"),
            "working_volume_max": to_si_quantity(200.0, "L", "working_volume_max", "vendor_datasheet"),
            "vessel_inner_diameter": to_si_quantity(0.55, "m", "vessel_inner_diameter", "vendor_datasheet"),
            "liquid_height_at_working_volume": to_si_quantity(0.85, "m", "liquid_height_at_working_volume", "manual_entry"),
            "impeller_diameter": to_si_quantity(0.25, "m", "impeller_diameter", "vendor_datasheet"),
            "impeller_power_number": to_si_quantity(5.0, "dimensionless", "impeller_power_number", "vendor_datasheet"),
            "agitation_speed_min": to_si_quantity(50.0, "rpm", "agitation_speed_min", "vendor_datasheet"),
            "agitation_speed_max": to_si_quantity(400.0, "rpm", "agitation_speed_max", "vendor_datasheet"),
            "motor_power_limit": to_si_quantity(1500.0, "W", "motor_power_limit", "vendor_datasheet"),
            "gas_flow_min": to_si_quantity(10.0, "L/min", "gas_flow_min", "vendor_datasheet"),
            "gas_flow_max": to_si_quantity(200.0, "L/min", "gas_flow_max", "vendor_datasheet"),
        },
        kla_evidence=[],
    )

    proc = ProcessSummary(
        batch_ids=["batch-1"],
        operating={
            "agitation_speed": to_si_quantity(500.0, "rpm", "agitation_speed", "sensor"),
            "airflow": to_si_quantity(1.0, "L/min", "airflow", "sensor"),
            "working_volume": to_si_quantity(2.0, "L", "working_volume", "manual_entry"),
            "temperature": to_si_quantity(37.0, "degC", "temperature", "sensor"),
        },
        extremes={
            "do_min": to_si_quantity(18.0, "% air sat", "dissolved_oxygen", "sensor"),
            "our_max": to_si_quantity(25.0, "mmol/(L*h)", "our", "lab_assay"),
        },
    )

    med = MediumProperties(
        name="M9-mod",
        density=to_si_quantity(1000.0, "kg/m^3", "density", "user_assumption"),
        viscosity=to_si_quantity(0.001, "Pa*s", "viscosity", "user_assumption"),
        oxygen_saturation_concentration=to_si_quantity(
            0.20, "mmol/L", "oxygen_saturation_concentration", "user_assumption"
        ),
    )

    scen = ScenarioConfig(
        criteria=[
            CriterionSelection(criterion_id="S-PV", is_primary=True),
            CriterionSelection(criterion_id="S-TIP", is_primary=False),
            CriterionSelection(criterion_id="S-KLA", is_primary=False),
        ],
        aeration_basis="S-VVM",
        target_working_volume=to_si_quantity(150.0, "L", "working_volume", "manual_entry"),
        constraints={
            "min_do_required": to_si_quantity(20.0, "% air sat", "min_do_required", "user_assumption"),
            "max_tip_speed": to_si_quantity(2.0, "m/s", "max_tip_speed", "user_assumption"),
        },
        thresholds=ThresholdConfig(),
    )

    return AssessmentInput(
        source_vessel=src_vessel,
        target_vessel=tgt_vessel,
        process=proc,
        medium=med,
        scenario=scen,
        is_synthetic=True,
    )
