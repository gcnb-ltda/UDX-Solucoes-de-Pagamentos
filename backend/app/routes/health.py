from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "udx-payments-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
