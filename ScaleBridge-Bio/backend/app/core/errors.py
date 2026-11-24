"""Standard error classes and exception handling (docs/08_API_SPECIFICATION.md §2)."""

from typing import Any
from fastapi import HTTPException, status

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

class EntityNotFoundError(ApiError):
    def __init__(self, entity_name: str, entity_id: str) -> None:
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code="NOT_FOUND",
            message=f"{entity_name} '{entity_id}' not found",
        )

class ConflictError(ApiError):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code="CONFLICT",
            message=message,
        )

class ValidationError(ApiError):
    def __init__(self, message: str, details: list[dict[str, Any]] | None = None) -> None:
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message=message,
            details=details,
        )
