"""Tests for Domain F: Infrastructure, Security, Storage, Health, and Backups.

Owner: Person 4 (Reporting, DevOps and Quality Lead).
Tests:
- Object storage abstraction (local filesystem and sha256 integrity).
- Health check endpoints (/api/v1/health/live and /api/v1/health/ready).
- Database backup and recovery integrity verification.
"""

from __future__ import annotations

import gzip
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.backup import backup_database, verify_backup_integrity
from app.core.storage import object_store
from app.main import app


def test_object_store_put_and_get(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test object store put_bytes, get_bytes, and SHA-256 computation."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "local_storage_path", str(tmp_path))

    data = b"Hello ScaleBridge Storage Test Content 2026"
    key = "test_folder/sample.txt"

    sha256 = object_store.put_bytes(key, data, content_type="text/plain")
    assert len(sha256) == 64

    retrieved = object_store.get_bytes(key)
    assert retrieved == data


def test_object_store_missing_file_raises(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test object store raises FileNotFoundError for nonexistent keys."""
    from app.core.config import settings

    monkeypatch.setattr(settings, "local_storage_path", str(tmp_path))

    with pytest.raises(FileNotFoundError):
        object_store.get_bytes("nonexistent_path/file.dat")


def test_health_live_endpoint() -> None:
    """Health liveness endpoint returns status: ok."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/health/live")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"


def test_health_ready_endpoint() -> None:
    """Health readiness endpoint verifies DB connection."""
    with TestClient(app) as client:
        resp = client.get("/api/v1/health/ready")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ready"


def test_database_backup_and_verification(tmp_path: Path) -> None:
    """Test creating a compressed backup archive and validating its SHA-256 checksum."""
    backup_path = backup_database(destination_dir=tmp_path)
    assert backup_path.exists()
    assert backup_path.name.endswith(".gz")

    # Verify SHA-256 sidecar file exists
    sha_file = tmp_path / f"{backup_path.name}.sha256"
    assert sha_file.exists()

    # Verify integrity routine returns True
    assert verify_backup_integrity(backup_path) is True

    # Test reading back uncompressed content
    with gzip.open(backup_path, "rb") as f:
        content = f.read()
        assert len(content) > 0
