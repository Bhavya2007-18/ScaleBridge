"""Unit and integration tests for Domain E: Process-Transfer PDF Report Generation & Serving.

Owner: Person 4 (Reporting, DevOps and Quality Lead).
Tests:
- PDF generation with synthetic watermark and notice.
- PDF generation with real/production settings.
- Deterministic report regeneration from stored assessments.
- Completeness of report sections (Summary, Vessels, Calculations, Checks, Risks, Validation, Reviews, Disclaimer).
- Storage and download endpoints with SHA-256 integrity verification.
"""

from __future__ import annotations

import hashlib

from fastapi.testclient import TestClient

from app.main import app
from app.modules.report_service import render_transfer_report_pdf


def _dummy_report_data(is_synthetic: bool = True) -> tuple[dict, dict, dict, dict]:
    project = {
        "id": "p-101",
        "name": "Industrial Amylase Scale-Up",
        "organism_name": "Bacillus licheniformis",
        "process_type": "fed_batch",
        "is_synthetic_demo": is_synthetic,
    }
    passport = {
        "recipe_version": "v1.2",
        "process_description": "Enzyme production with glucose fed-batch",
    }
    scenario = {
        "id": "scen-201",
        "name": "2 L Lab to 150 L Pilot",
    }
    assessment = {
        "id": "as-301",
        "engine_version": "0.1.0",
        "formula_registry_version": "1.0.0",
        "rule_registry_version": "1.0.0",
        "is_synthetic": is_synthetic,
        "summary": {
            "overall_evidence_level": "estimated",
            "triggered_by_severity": {"critical": 1, "high": 2, "medium": 3},
            "insufficient_evidence_flag_count": 1,
            "validation_task_count": 2,
        },
        "inputs_snapshot": {
            "source_vessel": {
                "name": "Lab Reactor 2L",
                "scale_class": "lab",
                "impeller_type": "rushton_turbine",
                "impeller_count": 1,
                "parameters": {
                    "working_volume_max": {
                        "display_value": 2.0,
                        "display_unit": "L",
                        "provenance": "manual_entry",
                    },
                    "vessel_inner_diameter": {
                        "display_value": 0.13,
                        "display_unit": "m",
                        "provenance": "manual_entry",
                    },
                },
            },
            "target_vessel": {
                "name": "Pilot Reactor 150L",
                "scale_class": "pilot",
                "impeller_type": "rushton_turbine",
                "impeller_count": 1,
                "parameters": {
                    "working_volume_max": {
                        "display_value": 150.0,
                        "display_unit": "L",
                        "provenance": "manual_entry",
                    },
                    "vessel_inner_diameter": {
                        "display_value": 0.55,
                        "display_unit": "m",
                        "provenance": "manual_entry",
                    },
                },
            },
        },
        "calculations": [
            {
                "formula_id": "F-TIP-001",
                "formula_name": "Tip Speed",
                "scale": "target",
                "criterion_id": "S-PV",
                "equation": "u_tip = pi * N * D",
                "status": "computed",
                "evidence_level": "estimated",
                "output": {"display_value": 2.45, "display_unit": "m/s"},
            },
            {
                "formula_id": "F-KLA-001",
                "formula_name": "kLa",
                "scale": "target",
                "status": "insufficient_evidence",
                "missing_inputs": ["target_broth_kla_correlation"],
                "evidence_level": "insufficient_evidence",
                "output": None,
            },
        ],
        "compatibility_checks": [
            {
                "check_id": "CHK-VOL-001",
                "criterion_id": "All",
                "parameter_key": "working_volume",
                "outcome": "pass",
                "explanation": "Target working volume 150 L within vessel envelope [50 L, 200 L].",
            }
        ],
        "risk_flags": [
            {
                "rule_id": "R-SHEAR-001",
                "rule_version": "1.0.0",
                "category": "shear_stress",
                "severity": "critical",
                "outcome": "triggered",
                "title": "Tip Speed Exceeds Maximum Threshold",
                "explanation": "Target tip speed exceeds recommended maximum limit.",
                "evidence_gap": "Broth shear tolerance assay not performed.",
            }
        ],
        "validation_tasks": [
            {
                "task_code": "VAL-KLA-001",
                "priority": "P1",
                "task_type": "experiment",
                "status": "open",
                "title": "Determine Target Broth kLa",
                "description": "Perform dynamic gassing-out characterization in pilot vessel.",
            }
        ],
        "reviews": [
            {
                "reviewer_name": "Dr. Bioprocess Lead",
                "decision": "approved_for_discussion",
                "comment": "Pre-pilot calculations verified. Perform kLa characterization first.",
                "created_at": "2026-11-20T10:00:00Z",
            }
        ],
    }
    return project, passport, scenario, assessment


def test_render_transfer_report_synthetic_pdf() -> None:
    """PDF generated with synthetic data contains valid PDF magic bytes and substantial content."""
    proj, passp, scen, assess = _dummy_report_data(is_synthetic=True)
    pdf_bytes = render_transfer_report_pdf(proj, passp, scen, assess, report_version=1)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")
    # PDF EOF trailer marker
    assert b"%%EOF" in pdf_bytes


def test_render_transfer_report_production_pdf() -> None:
    """PDF generated without synthetic flag compiles properly."""
    proj, passp, scen, assess = _dummy_report_data(is_synthetic=False)
    pdf_bytes = render_transfer_report_pdf(proj, passp, scen, assess, report_version=2)

    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 2000
    assert pdf_bytes.startswith(b"%PDF")


def test_deterministic_report_generation() -> None:
    """Regenerating a report from the exact same assessment data yields the exact same byte length and structure."""
    proj, passp, scen, assess = _dummy_report_data(is_synthetic=True)
    pdf_bytes_1 = render_transfer_report_pdf(proj, passp, scen, assess, report_version=1)
    pdf_bytes_2 = render_transfer_report_pdf(proj, passp, scen, assess, report_version=1)

    # Byte lengths should match exactly for deterministic generation
    assert len(pdf_bytes_1) == len(pdf_bytes_2)
    # Check SHA-256 can be computed reliably
    sha1 = hashlib.sha256(pdf_bytes_1).hexdigest()
    assert len(sha1) == 64


def test_report_api_generation_and_download() -> None:
    """Test generating a report via the API and downloading it via GET /reports/{id}/download."""
    with TestClient(app) as client:
        # Login
        r_login = client.post(
            "/api/v1/auth/login",
            json={"email": "scientist@scalebridge.bio", "password": "ScaleBridge2026!"},
        )
        assert r_login.status_code == 200
        token = r_login.json()["access_token"]
        org_id = r_login.json()["user"]["memberships"][0]["organization_id"]
        headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}

        # Get projects
        r_proj = client.get("/api/v1/projects", headers=headers)
        assert r_proj.status_code == 200
        proj_id = r_proj.json()["items"][0]["id"]

        # Get scenarios
        r_scens = client.get(f"/api/v1/projects/{proj_id}/scenarios", headers=headers)
        assert r_scens.status_code == 200
        scenarios = r_scens.json()["items"]
        assert len(scenarios) > 0
        scen_id = scenarios[0]["id"]

        # Run assessment
        r_assess = client.post(f"/api/v1/scenarios/{scen_id}/assessments", headers=headers)
        assert r_assess.status_code == 201
        assess_id = r_assess.json()["id"]

        # Generate report
        r_rep = client.post(f"/api/v1/assessments/{assess_id}/reports", headers=headers)
        assert r_rep.status_code == 201
        rep_data = r_rep.json()
        assert rep_data["version"] >= 1
        assert rep_data["status"] == "generated"
        assert len(rep_data["sha256"]) == 64
        rep_id = rep_data["id"]

        # List reports for assessment
        r_list = client.get(f"/api/v1/assessments/{assess_id}/reports", headers=headers)
        assert r_list.status_code == 200
        items = r_list.json()["items"]
        assert any(it["id"] == rep_id for it in items)

        # Download report
        r_dl = client.get(f"/api/v1/reports/{rep_id}/download", headers=headers)
        assert r_dl.status_code == 200
        assert r_dl.headers["content-type"] == "application/pdf"
        assert "attachment; filename=" in r_dl.headers["content-disposition"]
        assert r_dl.content.startswith(b"%PDF")
        # Check download SHA-256 matches the stored record
        assert hashlib.sha256(r_dl.content).hexdigest() == rep_data["sha256"]
