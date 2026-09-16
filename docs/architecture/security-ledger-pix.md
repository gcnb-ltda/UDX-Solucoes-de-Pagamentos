# Security, Backoffice, Pix and Ledger Foundation

This milestone extends IAM with PostgreSQL-backed login/MFA rate limits, progressive lockout, single-use MFA recovery codes, immutable audit logs, JWT signing-key rotation through `kid`, AWS Secrets Manager support and separate encrypted-secret material.

The existing `/payments` endpoint now persists idempotent transactions in PostgreSQL. The Pix foundation adds payment accounts and `pending` outgoing Pix instructions; the raw Pix key is not stored, only an HMAC and its last four display characters.

The ledger is double-entry. Initial accounts are `1100 Settlement Cash` (asset) and `2100 Customer Funds` (liability). A development-only completion transition posts equal debit and credit entries. PostgreSQL triggers make both `ledger_entries` and `audit_logs` immutable against UPDATE/DELETE.

Backoffice endpoints include payment-account management, transaction listing, development-only Pix completion, trial balance and audit-log review. Before real Pix settlement, a regulated PSP/bank adapter, signed webhook verification, reconciliation, balance controls, reversals/refunds and four-eyes approval must be added.
