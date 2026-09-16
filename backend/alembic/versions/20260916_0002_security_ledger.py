"""security hardening, persistent transactions, pix and ledger

Revision ID: 20260916_0002
Revises: 20260916_0001
Create Date: 2026-09-16
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "20260916_0002"
down_revision: str | None = "20260916_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None
UUID = postgresql.UUID(as_uuid=True)


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("mfa_failed_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "users",
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "mfa_recovery_codes",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_mfa_recovery_codes_user_id", "mfa_recovery_codes", ["user_id"])
    op.create_index("ix_mfa_recovery_codes_code_hash", "mfa_recovery_codes", ["code_hash"])

    op.create_table(
        "auth_rate_limits",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("route", sa.String(40), nullable=False),
        sa.Column("key_hash", sa.String(64), nullable=False),
        sa.Column("bucket_start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "route",
            "key_hash",
            "bucket_start",
            name="uq_auth_rate_limit_bucket",
        ),
    )
    op.create_index(
        "ix_auth_rate_limits_lookup",
        "auth_rate_limits",
        ["route", "key_hash", "bucket_start"],
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", UUID, primary_key=True),
        sa.Column("company_id", UUID, sa.ForeignKey("companies.id", ondelete="SET NULL")),
        sa.Column("actor_user_id", UUID, sa.ForeignKey("users.id", ondelete="SET NULL")),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(60)),
        sa.Column("target_id", sa.String(100)),
        sa.Column("ip_address", sa.String(64)),
        sa.Column("user_agent", sa.String(300)),
        sa.Column(
            "metadata",
            sa.JSON(),
            nullable=False,
            server_default=sa.text("'{}'::json"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    audit_indexes = [
        ("ix_audit_logs_company_id", ["company_id"]),
        ("ix_audit_logs_actor_user_id", ["actor_user_id"]),
        ("ix_audit_logs_action", ["action"]),
        ("ix_audit_logs_created_at", ["created_at"]),
    ]
    for name, columns in audit_indexes:
        op.create_index(name, "audit_logs", columns)

    op.create_table(
        "payment_accounts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "company_id",
            UUID,
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_id", UUID, sa.ForeignKey("branches.id", ondelete="SET NULL")),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("currency = 'BRL'", name="ck_payment_accounts_currency_brl"),
    )
    op.create_index("ix_payment_accounts_company_id", "payment_accounts", ["company_id"])
    op.create_index("ix_payment_accounts_branch_id", "payment_accounts", ["branch_id"])

    op.create_table(
        "transactions",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "company_id",
            UUID,
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("branch_id", UUID, sa.ForeignKey("branches.id", ondelete="SET NULL")),
        sa.Column(
            "account_id",
            UUID,
            sa.ForeignKey("payment_accounts.id", ondelete="SET NULL"),
        ),
        sa.Column(
            "created_by_user_id",
            UUID,
            sa.ForeignKey("users.id", ondelete="SET NULL"),
        ),
        sa.Column("kind", sa.String(40), nullable=False),
        sa.Column("direction", sa.String(12), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("reference", sa.String(100)),
        sa.Column("description", sa.String(200)),
        sa.Column("external_id", sa.String(120)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
        sa.CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        sa.UniqueConstraint(
            "company_id",
            "idempotency_key",
            name="uq_transactions_company_idempotency",
        ),
    )
    transaction_indexes = [
        "company_id",
        "branch_id",
        "account_id",
        "created_by_user_id",
        "kind",
        "status",
        "external_id",
        "created_at",
    ]
    for column in transaction_indexes:
        op.create_index(f"ix_transactions_{column}", "transactions", [column])

    op.create_table(
        "pix_transfers",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "transaction_id",
            UUID,
            sa.ForeignKey("transactions.id", ondelete="CASCADE"),
            nullable=False,
            unique=True,
        ),
        sa.Column("pix_key_hash", sa.String(64), nullable=False),
        sa.Column("pix_key_last4", sa.String(8), nullable=False),
        sa.Column("counterparty_name", sa.String(160)),
        sa.Column("counterparty_tax_id", sa.String(14)),
        sa.Column("end_to_end_id", sa.String(80)),
        sa.Column("txid", sa.String(80)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "ix_pix_transfers_transaction_id",
        "pix_transfers",
        ["transaction_id"],
        unique=True,
    )
    op.create_index("ix_pix_transfers_end_to_end_id", "pix_transfers", ["end_to_end_id"])
    op.create_index("ix_pix_transfers_txid", "pix_transfers", ["txid"])

    op.create_table(
        "ledger_accounts",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "company_id",
            UUID,
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.String(30), nullable=False),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("account_type", sa.String(20), nullable=False),
        sa.Column("currency", sa.String(3), nullable=False, server_default="BRL"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint("currency = 'BRL'", name="ck_ledger_accounts_currency_brl"),
        sa.UniqueConstraint(
            "company_id",
            "code",
            name="uq_ledger_accounts_company_code",
        ),
    )
    op.create_index("ix_ledger_accounts_company_id", "ledger_accounts", ["company_id"])

    op.create_table(
        "ledger_entries",
        sa.Column("id", UUID, primary_key=True),
        sa.Column(
            "company_id",
            UUID,
            sa.ForeignKey("companies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "transaction_id",
            UUID,
            sa.ForeignKey("transactions.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column(
            "ledger_account_id",
            UUID,
            sa.ForeignKey("ledger_accounts.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("side", sa.String(6), nullable=False),
        sa.Column("amount", sa.Numeric(18, 2), nullable=False),
        sa.Column("description", sa.String(200)),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.CheckConstraint(
            "side IN ('debit','credit')",
            name="ck_ledger_entries_side",
        ),
        sa.CheckConstraint("amount > 0", name="ck_ledger_entries_amount_positive"),
        sa.UniqueConstraint(
            "transaction_id",
            "ledger_account_id",
            "side",
            name="uq_ledger_entries_tx_account_side",
        ),
    )
    ledger_indexes = [
        "company_id",
        "transaction_id",
        "ledger_account_id",
        "created_at",
    ]
    for column in ledger_indexes:
        op.create_index(f"ix_ledger_entries_{column}", "ledger_entries", [column])

    op.execute(
        """
        CREATE FUNCTION udx_prevent_immutable_mutation()
        RETURNS trigger AS $$
        BEGIN
            RAISE EXCEPTION '% is immutable', TG_TABLE_NAME;
        END;
        $$ LANGUAGE plpgsql;
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_audit_logs_immutable
        BEFORE UPDATE OR DELETE ON audit_logs
        FOR EACH ROW EXECUTE FUNCTION udx_prevent_immutable_mutation();
        """
    )
    op.execute(
        """
        CREATE TRIGGER trg_ledger_entries_immutable
        BEFORE UPDATE OR DELETE ON ledger_entries
        FOR EACH ROW EXECUTE FUNCTION udx_prevent_immutable_mutation();
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_ledger_entries_immutable ON ledger_entries")
    op.execute("DROP TRIGGER IF EXISTS trg_audit_logs_immutable ON audit_logs")
    op.execute("DROP FUNCTION IF EXISTS udx_prevent_immutable_mutation")
    tables = [
        "ledger_entries",
        "ledger_accounts",
        "pix_transfers",
        "transactions",
        "payment_accounts",
        "audit_logs",
        "auth_rate_limits",
        "mfa_recovery_codes",
    ]
    for table in tables:
        op.drop_table(table)
    op.drop_column("users", "locked_until")
    op.drop_column("users", "mfa_failed_count")
    op.drop_column("users", "failed_login_count")
