"""Unit tests for core security helpers."""

from __future__ import annotations

import pytest

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    hash_token,
)


def test_password_hash_roundtrip() -> None:
    password = "ScaleBridge2026!"
    hashed = hash_password(password)
    assert hashed != password
    assert verify_password(password, hashed) is True


def test_password_verify_wrong() -> None:
    hashed = hash_password("correct")
    assert verify_password("wrong", hashed) is False


def test_access_token_roundtrip() -> None:
    token, expires = create_access_token(user_id="user-1", email="a@b.com")
    assert expires > 0
    payload = decode_access_token(token)
    assert payload["sub"] == "user-1"
    assert payload["email"] == "a@b.com"
    assert payload["type"] == "access"


def test_access_token_wrong_type_rejected() -> None:
    from app.core.config import settings
    import jwt

    # Craft a token with type != access
    token = jwt.encode(
        {"sub": "u", "email": "e", "type": "refresh", "exp": 9999999999},
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(Exception):
        decode_access_token(token)


def test_refresh_token_hash() -> None:
    raw, hashed, expires = generate_refresh_token()
    assert raw and hashed and expires is not None
    assert hash_token(raw) == hashed
    assert hash_token("other") != hashed
