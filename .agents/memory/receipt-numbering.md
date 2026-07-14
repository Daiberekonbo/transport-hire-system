---
name: Receipt numbering design
description: How THMS assigns permanent, never-reused receipt numbers and what the ReceiptSequence model does.
---

## Rule
Receipt numbers are globally monotonic. The sequence counter NEVER resets between days and NEVER reuses a number, even if a payment is voided.

Format: `THMS-{YYYYMMDD}-{seq:06d}` (date = UTC date the receipt was issued).

Example run:
```
THMS-20260714-000001
THMS-20260714-000002
THMS-20260715-000003   ← new day; seq continues from 3, not 1
```

**Why:** Real accounting systems require a gapless, auditable sequence. Voided receipts become tombstones in the audit log but their numbers are permanently retired.

**How to apply:**
- `_generate_receipt(payment)` in `backend/routes/payments.py` calls `ReceiptSequence.next_number(date_str)` — must be inside an open session that the caller commits.
- `ReceiptSequence` lives in `backend/models/receipt_seq.py`. Single-row table (`receipt_sequence`). Seeded on startup by `_seed_receipt_seq()` in `backend/__init__.py`.
- Old payments (created before this system) keep their `RCPT-YYYYMM-#####` format untouched; only new payments get the `THMS-...` format.
- `with_for_update()` provides row-level locking on Postgres; silently degraded on SQLite (acceptable for single-server).
