from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db import get_db

router = APIRouter(tags=["health"])


def _base(status_value: str) -> dict[str, str]:
    return {
        "status": status_value,
        "service": "udx-payments-api",
        "timestamp": datetime.now(UTC).isoformat(),
    }


@router.get("/health")
@router.get("/health/live")
def health() -> dict[str, str]:
    return _base("ok")


@router.get("/health/ready")
def readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database is not ready",
        ) from exc
    return _base("ready")


@router.get("/health/financial")
def financial_readiness(db: Session = Depends(get_db)) -> dict[str, str]:
    readiness(db)
    if settings.payment_provider == "disabled":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Payment provider is disabled",
        )
    return {
        **_base("ready"),
        "payment_provider": settings.payment_provider,
    }
