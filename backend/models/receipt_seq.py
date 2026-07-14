"""
ReceiptSequence — global monotonic counter for receipt numbers.

One row, ever. The counter NEVER resets, NEVER reuses a number.
Even if a receipt is voided or deleted, the next number is always last_seq + 1.

Format: THMS-{YYYYMMDD}-{seq:06d}
Example: THMS-20260714-000001

Thread safety
-------------
Uses SELECT … FOR UPDATE on Postgres, and implicit write serialisation on
SQLite (acceptable for single-server deployments).  Because next_number() is
called inside the same SQLAlchemy session as the Payment flush/commit, the
sequence increment and the payment record land in one atomic transaction.
"""

from backend.extensions import db


class ReceiptSequence(db.Model):
    __tablename__ = "receipt_sequence"

    id       = db.Column(db.Integer, primary_key=True)
    last_seq = db.Column(db.Integer, nullable=False, default=0)

    # ── public API ────────────────────────────────────────────────────────────

    @classmethod
    def next_number(cls, date_str: str) -> str:
        """
        Atomically increment the global sequence and return a unique receipt
        number.  date_str must be in 'YYYYMMDD' format (e.g. '20260714').

        This must be called inside an open SQLAlchemy session that will be
        committed by the caller.  The sequence row is locked for the duration
        of the transaction on databases that support row-level locking.
        """
        try:
            row = cls.query.with_for_update().first()
        except Exception:
            row = cls.query.first()

        if row is None:
            row = cls(last_seq=0)
            db.session.add(row)
            db.session.flush()   # assign PK without committing

        row.last_seq += 1
        seq = row.last_seq
        return f"THMS-{date_str}-{seq:06d}"

    @classmethod
    def current(cls) -> int:
        """Return the last sequence number used (0 if none yet)."""
        row = cls.query.first()
        return row.last_seq if row else 0
