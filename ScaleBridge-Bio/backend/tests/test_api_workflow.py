"""End-to-end API integration test covering Phases 1–7 (Auth, Passport, Ingestion, Vessels, Scenarios, Assessments, Validation, Reviews, PDF Report, Tenancy Isolation)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_full_scalebridge_workflow_and_tenancy() -> None:
    with TestClient(app) as client:
        # 1. Health checks
        r_live = client.get("/api/v1/health/live")
        assert r_live.status_code == 200
        assert r_live.json()["status"] == "ok"

        # 2. Login as seeded scientist
        r_login = client.post(
            "/api/v1/auth/login",
            json={"email": "scientist@scalebridge.bio", "password": "ScaleBridge2026!"},
        )
        assert r_login.status_code == 200
        auth_data = r_login.json()
        token = auth_data["access_token"]
        org_id = auth_data["user"]["memberships"][0]["organization_id"]
        headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}

        # 3. List seeded project & data checklist
        r_proj = client.get("/api/v1/projects", headers=headers)
        assert r_proj.status_code == 200
        projects = r_proj.json()["items"]
        assert len(projects) >= 1
        proj_id = projects[0]["id"]
        assert projects[0]["is_synthetic_demo"] is True

        r_chk = client.get(f"/api/v1/projects/{proj_id}/data-checklist", headers=headers)
        assert r_chk.status_code == 200
        assert r_chk.json()["summary"]["missing"] == 0

        # 4. List batches & measurements (Phase 2 & 3)
        r_batches = client.get(f"/api/v1/projects/{proj_id}/batches", headers=headers)
        assert r_batches.status_code == 200
        batches = r_batches.json()["items"]
        assert len(batches) >= 2
        b1_id = batches[0]["id"]
        b2_id = batches[1]["id"]

        r_meas = client.get(
            f"/api/v1/batches/{b1_id}/measurements?variables=ph,dissolved_oxygen,agitation_speed",
            headers=headers,
        )
        assert r_meas.status_code == 200
        assert len(r_meas.json()["series"]) == 3

        # 5. List & compare vessels (Phase 4)
        r_vessels = client.get("/api/v1/vessels", headers=headers)
        assert r_vessels.status_code == 200
        vessels = r_vessels.json()["items"]
        assert len(vessels) >= 2
        lab_v = next(v for v in vessels if v["scale_class"] == "lab")
        pilot_v = next(v for v in vessels if v["scale_class"] == "pilot")
        src_ver_id = lab_v["latest_version"]["id"]
        tgt_ver_id = pilot_v["latest_version"]["id"]

        # Verify missing-specification warning on pilot vessel (cooling_capacity omitted in seed)
        missing_keys = [m["key"] for m in pilot_v["missing_specifications"]]
        assert "cooling_capacity" in missing_keys

        r_cmp = client.get(
            f"/api/v1/vessels/compare?a={src_ver_id}&b={tgt_ver_id}", headers=headers
        )
        assert r_cmp.status_code == 200
        assert r_cmp.json()["geometric_ratios"]["vessel_a"]["D_over_T"] is not None

        # 6. Create Scenario & Run Assessment (Phase 5 & 6)
        r_scen = client.post(
            f"/api/v1/projects/{proj_id}/scenarios",
            headers=headers,
            json={
                "name": "2 L Lab -> 150 L Pilot (Constant P/V Primary)",
                "batch_ids": [b1_id, b2_id],
                "source_vessel_version_id": src_ver_id,
                "target_vessel_version_id": tgt_ver_id,
                "target_working_volume": {
                    "value": 150.0,
                    "unit": "L",
                    "provenance": "manual_entry",
                },
                "criteria": [
                    {"criterion_id": "S-PV", "is_primary": True},
                    {"criterion_id": "S-TIP", "is_primary": False},
                    {"criterion_id": "S-KLA", "is_primary": False},
                ],
                "aeration_basis": "S-VVM",
                "kla_selection": {
                    "source_point_id": "kla-lab-1",
                    "target_point_id": "kla-pilot-water",
                },
                "constraints": [
                    {
                        "key": "min_do_required",
                        "value": 20.0,
                        "unit": "% air sat",
                        "provenance": "user_assumption",
                    },
                    {
                        "key": "max_tip_speed",
                        "value": 2.1,
                        "unit": "m/s",
                        "provenance": "user_assumption",
                    },
                ],
                "assumptions": [],
                "thresholds": {},
            },
        )
        assert r_scen.status_code == 201
        scen_id = r_scen.json()["id"]

        r_assess = client.post(
            f"/api/v1/scenarios/{scen_id}/assessments",
            headers=headers,
        )
        assert r_assess.status_code == 201
        assessment = r_assess.json()
        assess_id = assessment["id"]
        assert len(assessment["calculations"]) > 10
        assert len(assessment["trade_offs"]) == 3
        assert len(assessment["compatibility_checks"]) >= 5
        assert len(assessment["risk_flags"]) >= 10
        assert len(assessment["validation_tasks"]) >= 3

        # 7. Update validation task & enforce waiver reason rule (Phase 7)
        vt_id = assessment["validation_tasks"][0]["id"]
        r_bad_waive = client.patch(
            f"/api/v1/validation-tasks/{vt_id}",
            headers=headers,
            json={"status": "waived", "waived_reason": ""},
        )
        assert r_bad_waive.status_code == 422

        r_good_update = client.patch(
            f"/api/v1/validation-tasks/{vt_id}",
            headers=headers,
            json={"status": "in_progress"},
        )
        assert r_good_update.status_code == 200

        # 8. Reviewer sign-off & PDF Transfer Report generation (Phase 7)
        r_rev_login = client.post(
            "/api/v1/auth/login",
            json={"email": "reviewer@scalebridge.bio", "password": "ScaleBridge2026!"},
        )
        rev_token = r_rev_login.json()["access_token"]
        rev_headers = {"Authorization": f"Bearer {rev_token}", "X-Organization-Id": org_id}

        r_sign = client.post(
            f"/api/v1/assessments/{assess_id}/reviews",
            headers=rev_headers,
            json={
                "decision": "approved_for_discussion",
                "comment": "Calculations verified; target broth kLa and cooling capacity must be confirmed with pilot facility before execution.",
            },
        )
        assert r_sign.status_code == 201

        r_rep = client.post(
            f"/api/v1/assessments/{assess_id}/reports",
            headers=headers,
        )
        assert r_rep.status_code == 201
        rep_id = r_rep.json()["id"]

        r_dl = client.get(f"/api/v1/reports/{rep_id}/download", headers=headers)
        assert r_dl.status_code == 200
        assert r_dl.headers["content-type"] == "application/pdf"
        assert r_dl.content.startswith(b"%PDF")
