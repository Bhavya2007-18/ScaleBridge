"""FastAPI dependencies: database session, authentication, RBAC, and audit logging."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.models import AuditEvent, Membership, Organization, User
from app.db.session import get_db

_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthContext:
    """Authenticated user plus the tenant context selected by the request."""

    user: User
    organization: Organization
    role: str

    @property
    def organization_id(self) -> str:
        return self.organization.id


class ApiError(HTTPException):
    """Structured API error matching docs/08_API_SPECIFICATION.md section 2."""

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


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)] = None,
    db: Session = Depends(get_db),
) -> User:
    """Validate the Bearer access token and return the authenticated user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.get(User, str(user_id))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def get_auth_context(
    x_organization_id: Annotated[str | None, Header(alias="X-Organization-Id")] = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AuthContext:
    """Resolve the tenant membership and return the request's AuthContext."""
    if not x_organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="X-Organization-Id header required",
        )

    membership = (
        db.query(Membership)
        .filter(
            Membership.organization_id == x_organization_id,
            Membership.user_id == user.id,
        )
        .first()
    )
    if membership is None:
        # Deliberately return 404 so callers cannot probe for other tenants.
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    organization = db.get(Organization, x_organization_id)
    if organization is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    return AuthContext(user=user, organization=organization, role=membership.role)


def require_roles(*allowed_roles: str):
    """Dependency factory raising 403 unless the caller has one of the roles."""

    def _check(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
        if ctx.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient role",
            )
        return ctx

    return _check


def record_audit(
    db: Session,
    org_id: str | None = None,
    actor_id: str | None = None,
    action: str = "",
    entity_type: str = "",
    entity_id: str = "",
    details: dict[str, Any] | None = None,
    *,
    organization_id: str | None = None,
    actor_user_id: str | None = None,
) -> None:
    """Append an immutable audit event.

    Both positional and keyword forms are supported because the endpoint layer
    uses the compact positional form.
    """
    event = AuditEvent(
        organization_id=org_id if org_id is not None else organization_id,
        actor_user_id=actor_id if actor_id is not None else actor_user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details or {},
    )
    db.add(event)
    db.flush()


__all__ = [
    "ApiError",
    "AuthContext",
    "get_auth_context",
    "get_current_user",
    "get_db",
    "record_audit",
    "require_roles",
]
