"""Integration test for the end-to-end assessment workflow (via public API)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, email: str = "scientist@scalebridge.bio") -> tuple[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "ScaleBridge2026!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    org_id = r.json()["user"]["memberships"][0]["organization_id"]
    return token, org_id


def test_end_to_end_assessment_workflow() -> None:
    with TestClient(app) as client:
        token, org_id = _login(client)
        headers = {"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}

        projects = client.get("/api/v1/projects", headers=headers).json()["items"]
        assert projects
        proj_id = projects[0]["id"]

        batches = client.get(f"/api/v1/projects/{proj_id}/batches", headers=headers).json()["items"]
        assert len(batches) >= 2
        b_ids = [batches[0]["id"], batches[1]["id"]]

        vessels = client.get("/api/v1/vessels", headers=headers).json()["items"]
        lab_v = next(v for v in vessels if v["scale_class"] == "lab")
        pilot_v = next(v for v in vessels if v["scale_class"] == "pilot")
        src_ver = lab_v["latest_version"]["id"]
        tgt_ver = pilot_v["latest_version"]["id"]

        r_scen = client.post(
            f"/api/v1/projects/{proj_id}/scenarios",
            headers=headers,
            json={
                "name": "Integration assessment scenario",
                "batch_ids": b_ids,
                "source_vessel_version_id": src_ver,
                "target_vessel_version_id": tgt_ver,
                "target_working_volume": {"value": 150.0, "unit": "L", "provenance": "manual_entry"},
                "criteria": [{"criterion_id": "S-PV", "is_primary": True}],
                "aeration_basis": "S-VVM",
                "kla_selection": {"source_point_id": "kla-lab-1", "target_point_id": "kla-pilot-water"},
                "constraints": [],
                "assumptions": [],
                "thresholds": {},
            },
        )
        assert r_scen.status_code == 201
        scen_id = r_scen.json()["id"]

        r_assess = client.post(f"/api/v1/scenarios/{scen_id}/assessments", headers=headers)
        assert r_assess.status_code == 201
        assessment = r_assess.json()
        assert assessment["id"] is not None
        assert assessment["status"] == "completed"
        assert len(assessment["calculations"]) > 0
        assert len(assessment["validation_tasks"]) > 0
