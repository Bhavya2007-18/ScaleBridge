"""Pure unit tests for Equipment Compatibility, Risk Rules, and Validation Planner (docs/12, 13, 14)."""

from __future__ import annotations

from scalebridge_science.contracts import (
    AssessmentInput,
    CriterionSelection,
    MediumProperties,
    ProcessSummary,
    ScenarioConfig,
    ThresholdConfig,
    VesselSpec,
)
from scalebridge_science.criteria import evaluate_criteria_and_calculations
from scalebridge_science.readiness import (
    RULE_REGISTRY,
    evaluate_compatibility_checks,
    evaluate_risk_rules,
    generate_validation_tasks,
    inspect_missing_vessel_specs,
)
from scalebridge_science.units import to_si_quantity


def test_rule_registry_metadata() -> None:
    expected_rules = [
        "R-OXY-001",
        "R-OXY-002",
        "R-OXY-003",
        "R-MIX-001",
        "R-MIX-002",
        "R-MIX-003",
        "R-MIX-004",
        "R-THM-001",
        "R-DAT-001",
        "R-DAT-002",
        "R-EQP-001",
    ]
    for rid in expected_rules:
        assert rid in RULE_REGISTRY, f"Rule {rid} not found in RULE_REGISTRY"
        meta = RULE_REGISTRY[rid]
        assert meta.rule_id == rid
        assert meta.category in ("oxygen_transfer", "mixing", "thermal", "data", "equipment")


def test_inspect_missing_vessel_specs() -> None:
    bare_vessel = VesselSpec(
        vessel_version_id="bare-1",
        name="Incomplete Vessel",
        parameters={},
    )
    missing = inspect_missing_vessel_specs(bare_vessel)
    assert len(missing) >= 12
    keys = {m["key"] for m in missing}
    assert "working_volume_min" in keys
    assert "impeller_diameter" in keys
    assert "kla_evidence" in keys


def test_compatibility_checks_outcomes() -> None:
    vessel = VesselSpec(
        vessel_version_id="tgt-1",
        name="Target Vessel",
        parameters={
            "working_volume_min": to_si_quantity(10.0, "L", "working_volume_min"),
            "working_volume_max": to_si_quantity(100.0, "L", "working_volume_max"),
            "agitation_speed_min": to_si_quantity(50.0, "rpm", "agitation_speed_min"),
            "agitation_speed_max": to_si_quantity(500.0, "rpm", "agitation_speed_max"),
            "vessel_inner_diameter": to_si_quantity(0.4, "m", "vessel_inner_diameter"),
            "impeller_diameter": to_si_quantity(0.15, "m", "impeller_diameter"),
            "impeller_power_number": to_si_quantity(5.0, "dimensionless", "impeller_power_number"),
            "motor_power_limit": to_si_quantity(2000.0, "W", "motor_power_limit"),
            "gas_flow_min": to_si_quantity(5.0, "L/min", "gas_flow_min"),
            "gas_flow_max": to_si_quantity(100.0, "L/min", "gas_flow_max"),
        },
    )

    # Within bounds -> compatible
    proc = ProcessSummary(
        operating={
            "working_volume": to_si_quantity(50.0, "L", "working_volume"),
            "agitation_speed": to_si_quantity(200.0, "rpm", "agitation_speed"),
            "airflow": to_si_quantity(25.0, "L/min", "airflow"),
        }
    )
    scen = ScenarioConfig(
        criteria=[CriterionSelection(criterion_id="S-TIP", is_primary=True)],
        aeration_basis="S-VVM",
        target_working_volume=to_si_quantity(50.0, "L", "working_volume"),
    )
    inp = AssessmentInput(
        source_vessel=vessel,
        target_vessel=vessel,
        process=proc,
        medium=MediumProperties(),
        scenario=scen,
    )
    _calcs, trade_offs = evaluate_criteria_and_calculations(inp)
    checks = evaluate_compatibility_checks(inp, trade_offs)

    vol_check = next(c for c in checks if c.check_id == "C-VOLUME-RANGE")
    assert vol_check.outcome == "compatible"

    # Beyond bounds -> incompatible
    scen_over = ScenarioConfig(
        criteria=[CriterionSelection(criterion_id="S-TIP", is_primary=True)],
        aeration_basis="S-VVM",
        target_working_volume=to_si_quantity(150.0, "L", "working_volume"),
    )
    inp_over = AssessmentInput(
        source_vessel=vessel,
        target_vessel=vessel,
        process=proc,
        medium=MediumProperties(),
        scenario=scen_over,
    )
    _, trade_offs_over = evaluate_criteria_and_calculations(inp_over)
    checks_over = evaluate_compatibility_checks(inp_over, trade_offs_over)
    vol_check_over = next(c for c in checks_over if c.check_id == "C-VOLUME-RANGE")
    assert vol_check_over.outcome == "incompatible"


def test_validation_planner_task_generation() -> None:
    src_vessel = VesselSpec(
        vessel_version_id="src-1",
        name="Source",
        parameters={
            "working_volume_min": to_si_quantity(1.0, "L", "working_volume_min"),
            "working_volume_max": to_si_quantity(2.0, "L", "working_volume_max"),
            "vessel_inner_diameter": to_si_quantity(0.13, "m", "vessel_inner_diameter"),
            "impeller_diameter": to_si_quantity(0.05, "m", "impeller_diameter"),
            "impeller_power_number": to_si_quantity(5.0, "dimensionless", "impeller_power_number"),
        },
    )
    tgt_vessel = VesselSpec(
        vessel_version_id="tgt-1",
        name="Target Incomplete",
        parameters={
            "working_volume_min": to_si_quantity(50.0, "L", "working_volume_min"),
            "working_volume_max": to_si_quantity(200.0, "L", "working_volume_max"),
            "vessel_inner_diameter": to_si_quantity(0.5, "m", "vessel_inner_diameter"),
            "impeller_diameter": to_si_quantity(0.2, "m", "impeller_diameter"),
            "impeller_power_number": to_si_quantity(5.0, "dimensionless", "impeller_power_number"),
        },
        kla_evidence=[],
    )
    proc = ProcessSummary(
        operating={
            "working_volume": to_si_quantity(2.0, "L", "working_volume"),
            "agitation_speed": to_si_quantity(500.0, "rpm", "agitation_speed"),
            "airflow": to_si_quantity(1.0, "L/min", "airflow"),
        },
        extremes={
            "do_min": to_si_quantity(15.0, "% air sat", "dissolved_oxygen"),
        },
    )
    scen = ScenarioConfig(
        criteria=[CriterionSelection(criterion_id="S-PV", is_primary=True)],
        aeration_basis="S-VVM",
        target_working_volume=to_si_quantity(100.0, "L", "working_volume"),
        constraints={
            "min_do_required": to_si_quantity(20.0, "% air sat", "min_do_required"),
        },
        thresholds=ThresholdConfig(),
    )
    inp = AssessmentInput(
        source_vessel=src_vessel,
        target_vessel=tgt_vessel,
        process=proc,
        medium=MediumProperties(density=to_si_quantity(1000.0, "kg/m^3", "density")),
        scenario=scen,
    )
    _calcs, trade_offs = evaluate_criteria_and_calculations(inp)
    checks = evaluate_compatibility_checks(inp, trade_offs)
    flags = evaluate_risk_rules(inp, _calcs, trade_offs, checks)
    tasks = generate_validation_tasks(flags, checks)

    assert len(tasks) > 0
    # Every task must have an action, priority, and rationale
    for task in tasks:
        assert task.priority in ("P1", "P2", "P3")
        assert len(task.title) > 0
        assert len(task.description) > 0
