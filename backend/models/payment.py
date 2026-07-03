"""
Payment — records a single payment event against a hire-purchase contract.

Receipt numbering
-----------------
Receipt numbers are auto-generated after INSERT (requires the payment.id):
    RCPT-{YYYYMM}-{id:05d}    e.g.  RCPT-202507-00042

Week coverage
-------------
week_from  — first week number this payment contributes toward (1-indexed)
week_to    — last week number fully covered (week_from-1 if partial/incomplete)

Example: weekly_amount = ₦32,000
    total_paid before = ₦128,000  (4 full weeks)
    this payment      = ₦96,000   (3 more weeks)
    week_from = 5,  week_to = 7

Partial payment example:
    total_paid before = ₦128,000  (4 full weeks)
    this payment      = ₦16,000   (half a week — doesn't complete week 5)
    week_from = 5,  week_to = 4   (week_to < week_from signals partial)
"""

from datetime import datetime
from backend.extensions import db


METHOD_LABELS = {
    "cash":     "Cash",
    "transfer": "Bank Transfer",
    "pos":      "POS Terminal",
}

METHOD_COLORS = {
    "cash":     "success",
    "transfer": "primary",
    "pos":      "info",
}


class Payment(db.Model):
    __tablename__ = "payments"

    id          = db.Column(db.Integer, primary_key=True)

    # ── Links ─────────────────────────────────────────────────────────────────
    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=False)
    driver_id   = db.Column(db.Integer, db.ForeignKey("drivers.id"),   nullable=False)

    # ── Core financial ────────────────────────────────────────────────────────
    amount      = db.Column(db.Numeric(15, 2), nullable=False)

    # ── Receipt & week tracking ───────────────────────────────────────────────
    receipt_number = db.Column(db.String(30), nullable=True, unique=True)
    week_from      = db.Column(db.Integer, nullable=True)   # first week covered
    week_to        = db.Column(db.Integer, nullable=True)   # last week fully paid

    # ── Legacy field kept for backward compat ─────────────────────────────────
    week_number    = db.Column(db.Integer, nullable=True)

    # ── Date / time ───────────────────────────────────────────────────────────
    payment_date   = db.Column(db.Date, default=datetime.utcnow().date)
    payment_time   = db.Column(db.Time, nullable=True)

    # ── Parties ───────────────────────────────────────────────────────────────
    sender         = db.Column(db.String(120), nullable=True)
    receiver       = db.Column(db.String(120), nullable=True)

    # ── Method ────────────────────────────────────────────────────────────────
    payment_method = db.Column(db.String(20), default="cash")
    pos_terminal   = db.Column(db.String(100), nullable=True)
    bank_name      = db.Column(db.String(100), nullable=True)
    reference      = db.Column(db.String(100), nullable=True)

    # ── Meta ──────────────────────────────────────────────────────────────────
    notes       = db.Column(db.Text, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def method_label(self):
        return METHOD_LABELS.get(self.payment_method, self.payment_method or "Cash")

    @property
    def method_color(self):
        return METHOD_COLORS.get(self.payment_method, "secondary")

    @property
    def is_partial(self):
        """True if this payment didn't fully complete its target week."""
        wf = self.week_from or 0
        wt = self.week_to or 0
        return wt < wf

    @property
    def full_weeks_covered(self):
        """Count of completely paid weeks in this payment."""
        wf = self.week_from or 0
        wt = self.week_to or 0
        return max(0, wt - wf + 1) if wt >= wf else 0

    @property
    def week_range_display(self):
        """Human-readable week coverage, e.g. 'Week 5', 'Weeks 5–7', or 'Part of Week 5'."""
        wf = self.week_from
        wt = self.week_to
        if wf is None:
            return "—"
        if self.is_partial:
            return f"Part of Week {wf}"
        if wt is None or wt == wf:
            return f"Week {wf}"
        return f"Weeks {wf}–{wt}"

    def __repr__(self):
        return f"<Payment #{self.id} ₦{self.amount} {self.receipt_number}>"
