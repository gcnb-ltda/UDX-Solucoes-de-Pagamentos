"""add provider events, pix charges and reconciliation

Revision ID: 20260916_0003
Revises: 20260916_0002
Create Date: 2026-09-16
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260916_0003"
down_revision: str | None = "20260916_0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None
UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.create_table(
        "pix_charges",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("transaction_id", UUID, sa.ForeignKey("transactions.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("provider_charge_id", sa.String(120), nullable=False),
        sa.Column("txid", sa.String(80)),
        sa.Column("copy_paste", sa.String(1024)),
        sa.Column("status", sa.String(30), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("provider", "provider_charge_id", name="uq_pix_charge_provider_id"),
    )
    for column in ["transaction_id", "provider", "provider_charge_id", "txid", "status"]:
        op.create_index(f"ix_pix_charges_{column}", "pix_charges", [column])

    op.create_table(
        "provider_events",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("provider", sa.String(40), nullable=False),
        sa.Column("external_event_id", sa.String(160), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("payload_sha256", sa.String(64), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(30), nullable=False, server_default="received"),
        sa.Column("error", sa.String(500)),
        sa.Column("received_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.UniqueConstraint("provider", "external_event_id", name="uq_provider_event_external_id"),
    )
    for column in ["provider", "external_event_id", "event_type", "status"]:
        op.create_index(f"ix_provider_events_{column}", "provider_events", [column])

    op.create_table(
        "reconciliation_records",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="SET NULL")),
        sa.Column("transaction_id", UUID, sa.ForeignKey("transactions.id", ondelete="SET NULL")),
        sa.Column("provider_event_id", UUID, sa.ForeignKey("provider_events.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(30), nullable=False),
        sa.Column("internal_amount", sa.Numeric(18, 2)),
        sa.Column("provider_amount", sa.Numeric(18, 2)),
        sa.Column("difference", sa.Numeric(18, 2)),
        sa.Column("notes", sa.String(500)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    for column in ["company_id", "transaction_id", "provider_event_id", "status", "created_at"]:
        op.create_index(f"ix_reconciliation_records_{column}", "reconciliation_records", [column])


def downgrade() -> None:
    op.drop_table("reconciliation_records")
    op.drop_table("provider_events")
    op.drop_table("pix_charges")
