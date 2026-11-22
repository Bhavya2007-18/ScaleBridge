"""Uniform error responses, authentication, organization scoping, RBAC, and audit helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import AuditEvent, Membership, Organization, User
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


class ApiError(HTTPException):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(
            status_code=status_code,
            detail={
                "error": {
                    "code": code,
                    "message": message,
                    "details": details or [],
                }
            },
        )


@dataclass
class AuthContext:
    user: User
    organization: Organization
    role: str


ROLE_RANK = {
    "viewer": 1,
    "scientist": 2,
    "reviewer": 2,
    "org_admin": 3,
}


def get_current_user(
    creds: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if creds is None or not creds.credentials:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "UNAUTHENTICATED", "Missing bearer token")
    try:
        payload = decode_access_token(creds.credentials)
    except Exception as exc:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED, "UNAUTHENTICATED", f"Invalid or expired token: {exc}"
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise ApiError(status.HTTP_401_UNAUTHORIZED, "UNAUTHENTICATED", "Invalid token payload")

    user = db.query(User).filter(User.id == str(user_id), User.is_active.is_(True)).first()
    if not user:
        raise ApiError(
            status.HTTP_401_UNAUTHORIZED, "UNAUTHENTICATED", "User not found or inactive"
        )
    return user


def get_auth_context(
    user: User = Depends(get_current_user),
    x_organization_id: str | None = Header(default=None, alias="X-Organization-Id"),
    db: Session = Depends(get_db),
) -> AuthContext:
    if x_organization_id:
        membership = (
            db.query(Membership)
            .filter(
                Membership.user_id == user.id,
                Membership.organization_id == x_organization_id,
            )
            .first()
        )
    else:
        membership = db.query(Membership).filter(Membership.user_id == user.id).first()

    if not membership:
        raise ApiError(
            status.HTTP_403_FORBIDDEN,
            "FORBIDDEN",
            "User is not a member of the requested organization",
        )

    org = db.query(Organization).filter(Organization.id == membership.organization_id).first()
    if not org:
        raise ApiError(status.HTTP_404_NOT_FOUND, "NOT_FOUND", "Organization not found")

    return AuthContext(user=user, organization=org, role=membership.role)


def require_roles(*allowed_roles: str):
    def _dep(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.role not in allowed_roles:
            raise ApiError(
                status.HTTP_403_FORBIDDEN,
                "FORBIDDEN",
                f"Role '{ctx.role}' does not have permission; requires one of {allowed_roles}",
            )
        return ctx

    return _dep


def record_audit(
    db: Session,
    organization_id: str | None,
    actor_user_id: str | None,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any] | None = None,
) -> None:
    ev = AuditEvent(
        organization_id=organization_id,
        actor_user_id=actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(ev)
