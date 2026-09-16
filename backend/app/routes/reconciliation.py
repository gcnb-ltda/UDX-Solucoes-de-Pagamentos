from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.dependencies import require_roles
from app.models import User, UserRole
from app.provider_models import ReconciliationRecord

router = APIRouter(prefix="/backoffice/reconciliation", tags=["backoffice"])


@router.get("/summary")
def reconciliation_summary(
    actor: User = Depends(require_roles(UserRole.admin, UserRole.finance, UserRole.accounting)),
    db: Session = Depends(get_db),
) -> dict[str, int]:
    records = list(
        db.scalars(
            select(ReconciliationRecord).where(
                ReconciliationRecord.company_id == actor.company_id
            )
        )
    )
    counts = Counter(record.status for record in records)
    return {
        "matched": counts.get("matched", 0),
        "mismatch": counts.get("mismatch", 0),
        "unmatched": counts.get("unmatched", 0),
        "total": len(records),
    }
