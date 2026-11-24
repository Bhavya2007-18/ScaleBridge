"""Ingestion API tests."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient) -> tuple[str, str, str]:
    r = client.post("/api/v1/auth/login", json={"email": "scientist@scalebridge.bio", "password": "ScaleBridge2026!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    org_id = r.json()["user"]["memberships"][0]["organization_id"]
    projects = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id}).json()["items"]
    return token, org_id, projects[0]["id"]


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_upload_rejects_bad_type(client: TestClient) -> None:
    token, org_id, proj_id = _login(client)
    r = client.post(
        f"/api/v1/projects/{proj_id}/files",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        files={"file": ("data.txt", io.BytesIO(b"hello"), "text/plain")},
    )
    assert r.status_code == 415


def test_upload_csv_accepted(client: TestClient) -> None:
    token, org_id, proj_id = _login(client)
    csv = b"Elapsed_h,pH,DO_pct_air_sat,Temperature_C,Agitation_rpm\n0,7.0,50,37,400\n1,7.0,48,37,400\n"
    r = client.post(
        f"/api/v1/projects/{proj_id}/files",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        files={"file": ("t.csv", io.BytesIO(csv), "text/csv")},
    )
    assert r.status_code == 201
    assert r.json()["status"] in ("uploaded", "parsed")
