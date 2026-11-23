"""RBAC and tenant isolation API tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


def _login(client: TestClient, email: str) -> tuple[str, str]:
    r = client.post("/api/v1/auth/login", json={"email": email, "password": "ScaleBridge2026!"})
    assert r.status_code == 200
    token = r.json()["access_token"]
    org_id = r.json()["user"]["memberships"][0]["organization_id"]
    return token, org_id


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_reviewer_cannot_create_project(client: TestClient) -> None:
    token, org_id = _login(client, "reviewer@scalebridge.bio")
    r = client.post(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id},
        json={"name": "X", "product_family": "enz", "organism_name": "org", "process_type": "fed_batch"},
    )
    assert r.status_code == 403


def test_scientist_can_list_projects(client: TestClient) -> None:
    token, org_id = _login(client, "scientist@scalebridge.bio")
    r = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id})
    assert r.status_code == 200
    assert "items" in r.json()


def test_cross_org_access_returns_404(client: TestClient) -> None:
    # scientist belongs to demo org; using a bogus org id must 404
    token, _ = _login(client, "scientist@scalebridge.bio")
    r = client.get(
        "/api/v1/projects",
        headers={"Authorization": f"Bearer {token}", "X-Organization-Id": "00000000-0000-0000-0000-000000000000"},
    )
    assert r.status_code == 404


def test_member_listing_requires_auth(client: TestClient) -> None:
    r = client.get("/api/v1/organizations/00000000-0000-0000-0000-000000000000/members")
    assert r.status_code == 401
