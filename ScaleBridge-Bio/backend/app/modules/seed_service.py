"""Idempotent seed routine creating a clearly labeled synthetic demonstration workspace (`is_synthetic_demo = True`).

Follows Blueprint p.5:
'Use clearly labeled synthetic or published data to demonstrate upload, vessel comparison,
risk explanation and report generation.'
"""

from __future__ import annotations

import math
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.core.storage import object_store
from app.db.models import (
    Batch,
    ColumnMapping,
    ConversionRecord,
    DataFile,
    Measurement,
    Membership,
    Organization,
    PassportVersion,
    Project,
    User,
    Vessel,
    VesselParameter,
    VesselVersion,
)
from app.modules.ingestion_service import (
    read_dataframe_from_bytes,
    validate_and_normalize_dataframe,
)
from scalebridge_science.units import to_si_quantity


def generate_synthetic_batch_csv(run_variant: int = 1) -> str:
    """Generate a deterministic, clearly labeled synthetic 2 L fed-batch fermentation CSV."""
    lines = [
        "Elapsed_h,pH,DO_pct_air_sat,Temperature_C,Agitation_rpm,Airflow_L_min,Feed_Rate_mL_h,Working_Volume_L,OUR_mmol_L_h,OD600,Biomass_DCW_g_L,Product_Titre_g_L"
    ]
    for step in range(0, 49):  # 0 to 24 hours in 0.5 h steps
        t_h = step * 0.5
        ph = 6.98 + 0.03 * math.sin(t_h * 0.4) + (0.01 if run_variant == 2 else 0.0)
        temp = 37.0 + 0.15 * math.cos(t_h * 0.5)
        rpm = 400.0 if t_h < 6.0 else (550.0 if t_h < 12.0 else 650.0)
        if run_variant == 2 and t_h >= 12.0:
            rpm = 620.0
        airflow = 1.0 if t_h < 8.0 else 1.5
        feed_ml_h = 0.0 if t_h < 6.0 else 18.0
        vol_l = 1.6 + (0.0 if t_h < 6.0 else (t_h - 6.0) * 0.018)
        # Microbial growth curve (synthetic)
        biomass = 0.5 + 28.0 / (1.0 + math.exp(-0.38 * (t_h - 11.0)))
        if run_variant == 2:
            biomass *= 0.96
        od600 = biomass * 2.6
        our = 4.0 + 36.0 * math.exp(-((t_h - 13.5) ** 2) / 28.0)
        do_pct = max(16.5 if run_variant == 1 else 18.2, 95.0 - 2.15 * our)
        titre = max(0.0, 0.0 if t_h < 5.0 else 8.4 / (1.0 + math.exp(-0.42 * (t_h - 15.0))))
        if run_variant == 2:
            titre *= 0.95

        lines.append(
            f"{t_h:.1f},{ph:.2f},{do_pct:.1f},{temp:.2f},{rpm:.0f},{airflow:.2f},{feed_ml_h:.1f},{vol_l:.3f},{our:.2f},{od600:.2f},{biomass:.2f},{titre:.2f}"
        )
    return "\n".join(lines) + "\n"


def seed_demo_workspace(db: Session) -> None:
    existing_org = db.query(Organization).filter(Organization.slug == "scalebridge-demo-bio").first()
    if existing_org:
        return

    org = Organization(
        name="ScaleBridge Demo Bioprocess Lab (Synthetic)",
        slug="scalebridge-demo-bio",
        data_retention_days=365,
    )
    db.add(org)
    db.flush()

    scientist = User(
        email="scientist@scalebridge.bio",
        password_hash=hash_password("ScaleBridge2026!"),
        full_name="Dr. Ananya Rao (Bioprocess Scientist)",
        is_active=True,
    )
    reviewer = User(
        email="reviewer@scalebridge.bio",
        password_hash=hash_password("ScaleBridge2026!"),
        full_name="Prof. Vikram Menon (Bioprocess Advisor)",
        is_active=True,
    )
    admin = User(
        email="admin@scalebridge.bio",
        password_hash=hash_password("ScaleBridge2026!"),
        full_name="Karthik Sharma (Process Dev Lead)",
        is_active=True,
    )
    db.add_all([scientist, reviewer, admin])
    db.flush()

    db.add_all(
        [
            Membership(organization_id=org.id, user_id=scientist.id, role="scientist"),
            Membership(organization_id=org.id, user_id=reviewer.id, role="reviewer"),
            Membership(organization_id=org.id, user_id=admin.id, role="org_admin"),
        ]
    )

    proj = Project(
        organization_id=org.id,
        name="Alkaline Protease AP-01 (2 L Lab to 200 L Pilot — Synthetic Demo)",
        product_family="industrial_enzyme",
        organism_name="Bacillus subtilis SB-104 (Synthetic Demo Strain)",
        strain_metadata={
            "strain_id": "SB-104-SYNTH",
            "selection_marker": "Antibiotic-free food-grade expression",
            "oxygen_requirement": "Strictly aerobic",
        },
        process_type="fed_batch",
        owner_user_id=scientist.id,
        is_synthetic_demo=True,
    )
    db.add(proj)
    db.flush()

    pv = PassportVersion(
        organization_id=org.id,
        project_id=proj.id,
        version=1,
        recipe_version="R-2026.1 (Synthetic Demo)",
        process_description="Aerobic glucose-limited fed-batch fermentation for extracellular alkaline protease production. Batch phase 0–6 h followed by exponential/constant glucose feeding.",
        organism_context={
            "organism_name": proj.organism_name,
            "critical_notes": "Sensitive to dissolved oxygen dips below 20% air saturation during induction phase.",
        },
        medium_context={
            "name": "Defined Mineral Salts + Glucose Feed (Synthetic Demo)",
            "density": to_si_quantity(1025.0, "kg/m^3", "density", "user_assumption").model_dump(),
            "viscosity": to_si_quantity(1.4, "mPa*s", "viscosity", "user_assumption").model_dump(),
            "oxygen_saturation_concentration": to_si_quantity(
                0.21, "mmol/L", "oxygen_saturation_concentration", "user_assumption"
            ).model_dump(),
        },
        process_parameters=[
            {
                "key": "temperature_setpoint",
                "value": 37.0,
                "unit": "degC",
                "provenance": "manual_entry",
                "value_nature": "measured",
                "note": "Controlled via jacket water",
            },
            {
                "key": "ph_setpoint",
                "value": 7.0,
                "unit": "pH",
                "provenance": "manual_entry",
                "value_nature": "measured",
                "note": "25% NH4OH / 2M H3PO4",
            },
            {
                "key": "do_setpoint",
                "value": 30.0,
                "unit": "% air sat",
                "provenance": "manual_entry",
                "value_nature": "measured",
                "note": "Maintained by agitation cascade 400-650 rpm",
            },
        ],
        material_context={"carbon_source": "Glucose 500 g/L sterile feed", "antifoam": "Silicone food-grade"},
        change_note="Seeded synthetic demonstration Process Passport",
        created_by=scientist.id,
    )
    db.add(pv)
    db.flush()

    # Create Lab 2 L Vessel & Pilot 200 L Vessel
    v_lab = Vessel(
        organization_id=org.id,
        name="BenchTop-2L Glass Bioreactor (Lab)",
        scale_class="lab",
        manufacturer="BioBench Glass (Demo)",
        model="BB-2000",
        location="R&D Fermentation Suite A",
    )
    v_pilot = Vessel(
        organization_id=org.id,
        name="Pilot-200L Stainless SIP Bioreactor",
        scale_class="pilot",
        manufacturer="InduFerment Engineering (Demo)",
        model="IF-200-SIP",
        location="Shared Biofoundry Pilot Hall",
    )
    db.add_all([v_lab, v_pilot])
    db.flush()

    ver_lab = VesselVersion(
        organization_id=org.id,
        vessel_id=v_lab.id,
        version=1,
        impeller_type="rushton_turbine",
        impeller_count=2,
        sparger_type="ring",
        instrumentation=["ph_probe", "do_probe", "temperature_probe", "offgas_analyzer", "balance_feed"],
        controls=["ph_control", "do_cascade_agitation", "do_cascade_airflow", "temperature_control", "feed_pump"],
        kla_evidence=[
            {
                "id": "kla-lab-1",
                "kla": {"value": 145.0, "unit": "1/h", "provenance": "lab_assay", "value_nature": "measured"},
                "agitation_speed": {"value": 650.0, "unit": "rpm", "provenance": "lab_assay"},
                "gas_flow": {"value": 1.5, "unit": "L/min", "provenance": "lab_assay"},
                "working_volume": {"value": 2.0, "unit": "L", "provenance": "lab_assay"},
                "medium_description": "Defined mineral medium at 37 °C",
                "method": "Dynamic gassing-out",
            }
        ],
        mixing_time_evidence=[
            {
                "id": "mix-lab-1",
                "mixing_time": {"value": 4.5, "unit": "s", "provenance": "lab_assay"},
                "method": "Acid/base pulse pH tracer at 600 rpm",
            }
        ],
        change_note="Documented 2 L benchtop vessel geometry and kLa",
        created_by=scientist.id,
    )

    ver_pilot = VesselVersion(
        organization_id=org.id,
        vessel_id=v_pilot.id,
        version=1,
        impeller_type="rushton_turbine",
        impeller_count=2,
        sparger_type="ring",
        instrumentation=["ph_probe", "do_probe", "temperature_probe", "pressure_sensor"],
        controls=["ph_control", "do_cascade_agitation", "do_cascade_airflow", "temperature_control", "feed_pump"],
        kla_evidence=[
            {
                "id": "kla-pilot-water",
                "kla": {"value": 92.0, "unit": "1/h", "provenance": "vendor_datasheet", "value_nature": "measured"},
                "agitation_speed": {"value": 250.0, "unit": "rpm", "provenance": "vendor_datasheet"},
                "gas_flow": {"value": 100.0, "unit": "L/min", "provenance": "vendor_datasheet"},
                "working_volume": {"value": 150.0, "unit": "L", "provenance": "vendor_datasheet"},
                "medium_description": "Deionized water factory acceptance test at 25 °C",
                "method": "Vendor FAT sulfite test",
            }
        ],
        mixing_time_evidence=[],
        change_note="Pilot 200 L vessel datasheet specs (cooling capacity & broth kLa pending)",
        created_by=scientist.id,
    )
    db.add_all([ver_lab, ver_pilot])
    db.flush()

    lab_params = [
        ("total_volume", 3.0, "L", "vendor_datasheet"),
        ("working_volume_min", 0.8, "L", "vendor_datasheet"),
        ("working_volume_max", 2.2, "L", "vendor_datasheet"),
        ("vessel_inner_diameter", 0.13, "m", "vendor_datasheet"),
        ("liquid_height_at_working_volume", 0.15, "m", "manual_entry"),
        ("impeller_diameter", 0.052, "m", "vendor_datasheet"),
        ("impeller_power_number", 5.0, "dimensionless", "published_correlation"),
        ("agitation_speed_min", 100.0, "rpm", "vendor_datasheet"),
        ("agitation_speed_max", 1200.0, "rpm", "vendor_datasheet"),
        ("motor_power_limit", 120.0, "W", "vendor_datasheet"),
        ("gas_flow_min", 0.2, "L/min", "vendor_datasheet"),
        ("gas_flow_max", 5.0, "L/min", "vendor_datasheet"),
        ("cooling_capacity", 250.0, "W", "vendor_datasheet"),
        ("temperature_min", 15.0, "degC", "vendor_datasheet"),
        ("temperature_max", 60.0, "degC", "vendor_datasheet"),
    ]
    for k, val, u, prov in lab_params:
        q = to_si_quantity(val, u, k, provenance=prov)  # type: ignore[arg-type]
        db.add(
            VesselParameter(
                organization_id=org.id,
                vessel_version_id=ver_lab.id,
                key=k,
                value_original=val,
                unit_original=u,
                value_si=q.value,
                unit_si=q.unit,
                provenance=q.provenance,
                value_nature=q.value_nature,
                source_reference="BB-2000 Datasheet",
            )
        )

    pilot_params = [
        ("total_volume", 250.0, "L", "vendor_datasheet"),
        ("working_volume_min", 70.0, "L", "vendor_datasheet"),
        ("working_volume_max", 200.0, "L", "vendor_datasheet"),
        ("vessel_inner_diameter", 0.56, "m", "vendor_datasheet"),
        ("liquid_height_at_working_volume", 0.82, "m", "manual_entry"),
        ("impeller_diameter", 0.22, "m", "vendor_datasheet"),
        ("impeller_power_number", 5.0, "dimensionless", "published_correlation"),
        ("agitation_speed_min", 40.0, "rpm", "vendor_datasheet"),
        ("agitation_speed_max", 320.0, "rpm", "vendor_datasheet"),
        ("motor_power_limit", 2200.0, "W", "vendor_datasheet"),
        ("gas_flow_min", 15.0, "L/min", "vendor_datasheet"),
        ("gas_flow_max", 180.0, "L/min", "vendor_datasheet"),
        ("temperature_min", 15.0, "degC", "vendor_datasheet"),
        ("temperature_max", 55.0, "degC", "vendor_datasheet"),
        # Note: cooling_capacity intentionally omitted on pilot vessel to demonstrate R-THM-001 & missing-spec warning
    ]
    for k, val, u, prov in pilot_params:
        q = to_si_quantity(val, u, k, provenance=prov)  # type: ignore[arg-type]
        db.add(
            VesselParameter(
                organization_id=org.id,
                vessel_version_id=ver_pilot.id,
                key=k,
                value_original=val,
                unit_original=u,
                value_si=q.value,
                unit_si=q.unit,
                provenance=q.provenance,
                value_nature=q.value_nature,
                source_reference="IF-200-SIP Spec Sheet",
            )
        )

    # Seed two synthetic batches via the ingestion pipeline
    mapping_cfg = {
        "sheet": "CSV",
        "header_row": 1,
        "timestamp": {"column": "Elapsed_h", "kind": "elapsed", "elapsed_unit": "h"},
        "batch_start": "2026-11-10T08:00:00Z",
        "columns": [
            {"source": "pH", "variable": "ph", "unit": "pH", "provenance": "sensor", "calibration_status": "calibrated_pre_run"},
            {"source": "DO_pct_air_sat", "variable": "dissolved_oxygen", "unit": "percent_air_saturation", "provenance": "sensor", "calibration_status": "calibrated_pre_run"},
            {"source": "Temperature_C", "variable": "temperature", "unit": "degC", "provenance": "sensor"},
            {"source": "Agitation_rpm", "variable": "agitation_speed", "unit": "rpm", "provenance": "sensor"},
            {"source": "Airflow_L_min", "variable": "airflow", "unit": "L/min", "provenance": "sensor"},
            {"source": "Feed_Rate_mL_h", "variable": "feed_rate", "unit": "mL/h", "provenance": "sensor"},
            {"source": "Working_Volume_L", "variable": "working_volume", "unit": "L", "provenance": "sensor"},
            {"source": "OUR_mmol_L_h", "variable": "our", "unit": "mmol/(L*h)", "provenance": "lab_assay"},
            {"source": "OD600", "variable": "od600", "unit": "OD600", "provenance": "lab_assay"},
            {"source": "Biomass_DCW_g_L", "variable": "biomass_dcw", "unit": "g/L", "provenance": "lab_assay"},
            {"source": "Product_Titre_g_L", "variable": "product_titre", "unit": "g/L", "provenance": "lab_assay"},
        ],
    }

    for run_idx, run_code in [(1, "LAB-2L-RUN-01 (Synthetic)"), (2, "LAB-2L-RUN-02 (Synthetic)")]:
        csv_text = generate_synthetic_batch_csv(run_variant=run_idx)
        csv_bytes = csv_text.encode("utf-8")
        fname = f"synthetic_ap01_2L_run0{run_idx}.csv"

        f_row = DataFile(
            organization_id=org.id,
            project_id=proj.id,
            original_filename=fname,
            content_type="text/csv",
            size_bytes=len(csv_bytes),
            sha256="",
            storage_key="",
            status="imported",
            is_synthetic=True,
            source_description="Seeded synthetic demonstration fermentation batch",
            uploaded_by=scientist.id,
        )
        db.add(f_row)
        db.flush()

        s_key = f"orgs/{org.id}/raw/{f_row.id}/{fname}"
        sha = object_store.put_bytes(s_key, csv_bytes, "text/csv")
        f_row.storage_key = s_key
        f_row.sha256 = sha

        cm = ColumnMapping(
            organization_id=org.id,
            data_file_id=f_row.id,
            name="Standard Synthetic 2L Export Mapping",
            is_template=True,
            mapping=mapping_cfg,
            created_by=scientist.id,
        )
        db.add(cm)

        df, _ = read_dataframe_from_bytes(csv_bytes, fname)
        res = validate_and_normalize_dataframe(df, mapping_cfg)
        f_row.last_quality_report = {
            "file_id": f_row.id,
            "rows_total": res["rows_total"],
            "rows_imported": res["rows_imported"],
            "variables": res["variables"],
            "issues": res["issues"],
            "conversions": res["conversions"],
            "blocking": False,
        }

        b_row = Batch(
            organization_id=org.id,
            project_id=proj.id,
            passport_version_id=pv.id,
            vessel_version_id=ver_lab.id,
            data_file_id=f_row.id,
            run_code=run_code,
            scale_label="2 L Lab",
            working_volume_original=1.9,
            working_volume_unit="L",
            working_volume_si=0.0019,
            start_time=res["start_time"],
            end_time=res["end_time"],
            operator="Dr. Ananya Rao",
            notes="Synthetic demonstration batch showing exponential feeding and peak oxygen demand at 13.5 h.",
            is_synthetic=True,
        )
        db.add(b_row)
        db.flush()

        for m in res["normalized_measurements"]:
            db.add(
                Measurement(
                    organization_id=org.id,
                    batch_id=b_row.id,
                    ts=m["ts"],
                    elapsed_s=m["elapsed_s"],
                    variable=m["variable"],
                    value_original=m["value_original"],
                    unit_original=m["unit_original"],
                    value_si=m["value_si"],
                    unit_si=m["unit_si"],
                    provenance=m["provenance"],
                    sensor_or_assay=m["sensor_or_assay"],
                    calibration_status=m["calibration_status"],
                    quality_flag=m["quality_flag"],
                    data_file_id=f_row.id,
                    source_row=m["source_row"],
                )
            )
        for conv in res["conversions"]:
            db.add(
                ConversionRecord(
                    organization_id=org.id,
                    data_file_id=f_row.id,
                    variable=conv["variable"],
                    from_unit=conv["from_unit"],
                    to_unit=conv["to_unit"],
                    method=conv["method"],
                    pint_version=conv["pint_version"],
                )
            )

    db.commit()
