from sqlalchemy.orm import Session
from app.models.tenant import Organization
from app.models.user import User, Membership
from app.models.project import Project, PassportVersion
from app.models.vessel import Vessel, VesselParameter
from app.models.scenario import Scenario
from app.core.security import get_password_hash

def seed_demo_data(db: Session) -> dict:
    """Seeds synthetic reference bioprocess demo data (CHO cell culture scale-up from 5L to 200L)."""
    # Check if already seeded
    existing_org = db.query(Organization).filter(Organization.slug == "demo-biologics").first()
    if existing_org:
        return {"status": "already_seeded", "organization_id": existing_org.id}

    org = Organization(
        name="Demo Biologics Corp (Synthetic)",
        slug="demo-biologics"
    )
    db.add(org)
    db.flush()

    user = User(
        email="lead.scientist@demobio.example",
        hashed_password=get_password_hash("Password123!"),
        full_name="Dr. Elena Vance (Synthetic Demo)",
        is_active=True
    )
    db.add(user)
    db.flush()

    membership = Membership(
        organization_id=org.id,
        user_id=user.id,
        role="admin"
    )
    db.add(membership)

    project = Project(
        tenant_id=org.id,
        name="mAb-104 Pilot Scale Transfer (Synthetic)",
        description="Monoclonal antibody mammalian cell culture transfer from 5L glass bioreactor to 200L pilot SUB.",
        organism="CHO-K1",
        target_molecule="IgG1 Monoclonal Antibody",
        expression_system="Suspension Mammalian Expression"
    )
    db.add(project)
    db.flush()

    passport = PassportVersion(
        project_id=project.id,
        version_number=1,
        critical_process_parameters={
            "temperature_c": 36.8,
            "ph_target": 7.1,
            "do_setpoint_percent": 40.0,
            "agitation_power_density_target_w_m3": 120.0
        },
        critical_quality_attributes={
            "titer_g_l": 3.8,
            "viability_at_harvest_pct": 88.0,
            "monomer_content_pct": 96.5
        },
        media_recipe={
            "basal_medium": "CD CHO Standard",
            "glucose_feed_g_l": 40.0
        },
        notes="Synthetic reference baseline"
    )
    db.add(passport)

    # 1. Source Vessel: 5L Lab Glass Bioreactor
    vessel_lab = Vessel(
        tenant_id=org.id,
        name="Sartorius Biostat B 5L (Synthetic Lab)",
        facility="Lab 3B - Benchtop",
        scale_category="lab",
        working_volume_min_l=1.5,
        working_volume_max_l=5.0,
        total_volume_l=6.5,
        aspect_ratio=1.6,
        impeller_count=2,
        impeller_types=["Marine Impeller", "Rushton Turbine"],
        baffle_count=4,
        sparger_type="Ring Sparger",
        max_rpm=600.0,
        max_power_w=300.0,
        max_gassing_vvm=2.0
    )
    db.add(vessel_lab)

    # 2. Target Vessel: 200L Pilot Single-Use Bioreactor
    vessel_pilot = Vessel(
        tenant_id=org.id,
        name="Thermo HyPerforma 200L SUB (Synthetic Pilot)",
        facility="Building 2 Pilot Plant",
        scale_category="pilot",
        working_volume_min_l=50.0,
        working_volume_max_l=200.0,
        total_volume_l=250.0,
        aspect_ratio=1.5,
        impeller_count=1,
        impeller_types=["Pitched-Blade Impeller"],
        baffle_count=0,
        sparger_type="Microsparger + Open Pipe",
        max_rpm=220.0,
        max_power_w=2500.0,
        max_gassing_vvm=1.0
    )
    db.add(vessel_pilot)
    db.flush()

    # Create baseline scenario
    scenario = Scenario(
        project_id=project.id,
        source_vessel_id=vessel_lab.id,
        target_vessel_id=vessel_pilot.id,
        target_working_volume_l=200.0,
        selected_criteria=["constant_p_v", "constant_tip_speed"],
        target_process_temperature_c=36.8,
        operating_parameters={"agitation_rpm": 120.0, "gas_flow_slpm": 40.0},
        notes="Synthetic primary scale-up transfer scenario"
    )
    db.add(scenario)

    db.commit()
    return {
        "status": "seeded",
        "organization_id": org.id,
        "project_id": project.id,
        "source_vessel_id": vessel_lab.id,
        "target_vessel_id": vessel_pilot.id,
        "scenario_id": scenario.id
    }
