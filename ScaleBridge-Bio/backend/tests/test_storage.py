"""Unit tests for object storage abstraction."""

from __future__ import annotations

import pytest

from app.core import storage as storage_mod
from app.core.storage import ObjectStore


def test_local_put_get_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage_mod.settings, "storage_backend", "local")
    monkeypatch.setattr(storage_mod.settings, "local_storage_path", str(tmp_path))
    store = ObjectStore()
    sha = store.put_bytes("orgs/o/file.csv", b"hello", "text/csv")
    assert len(sha) == 64
    assert store.get_bytes("orgs/o/file.csv") == b"hello"


def test_local_path_traversal_rejected(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(storage_mod.settings, "storage_backend", "local")
    monkeypatch.setattr(storage_mod.settings, "local_storage_path", str(tmp_path))
    store = ObjectStore()
    with pytest.raises(ValueError):
        store.put_bytes("../escape.txt", b"x")
    with pytest.raises(ValueError):
        store.get_bytes("../../etc/passwd")
