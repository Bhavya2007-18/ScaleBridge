"""API-level auth tests."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


def test_login_success(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "scientist@scalebridge.bio", "password": "ScaleBridge2026!"},
    )
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert body["user"]["email"] == "scientist@scalebridge.bio"
    assert body["user"]["memberships"]


def test_login_wrong_password(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "scientist@scalebridge.bio", "password": "wrong"},
    )
    assert r.status_code in (400, 401, 403)


def test_login_unknown_user(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "nobody@scalebridge.bio", "password": "x"},
    )
    assert r.status_code in (400, 401, 403, 404)


def test_me_requires_token(client: TestClient) -> None:
    r = client.get("/api/v1/me")
    assert r.status_code == 401


def test_me_with_token(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "scientist@scalebridge.bio", "password": "ScaleBridge2026!"},
    )
    token = r.json()["access_token"]
    org_id = r.json()["user"]["memberships"][0]["organization_id"]
    r2 = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}", "X-Organization-Id": org_id})
    assert r2.status_code == 200
    assert r2.json()["email"] == "scientist@scalebridge.bio"


def test_protected_endpoint_requires_org_header(client: TestClient) -> None:
    r = client.post(
        "/api/v1/auth/login",
        json={"email": "scientist@scalebridge.bio", "password": "ScaleBridge2026!"},
    )
    token = r.json()["access_token"]
    r2 = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 400


def test_invalid_token_rejected(client: TestClient) -> None:
    r = client.get(
        "/api/v1/projects",
        headers={"Authorization": "Bearer not-a-token", "X-Organization-Id": "x"},
    )
    assert r.status_code == 401
