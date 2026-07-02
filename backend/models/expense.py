"""
Expense — extra expenditure / loan advanced to a driver.

These are post-contract costs: vehicle repairs, accident damage, fines, etc.
An expense is always linked to a driver and optionally to a specific contract.
When linked to a contract, the amount is added to that contract's outstanding
balance automatically via Contract.total_extra_expenditure.

Status values
-------------
outstanding        — not yet repaid
partially_paid     — some of the amount has been recovered
paid               — fully recovered from the driver
"""

from datetime import datetime
from backend.extensions import db


class Expense(db.Model):
    __tablename__ = "expenses"

    id          = db.Column(db.Integer, primary_key=True)

    # ── Links ─────────────────────────────────────────────────────────────────
    driver_id   = db.Column(db.Integer, db.ForeignKey("drivers.id"),   nullable=False)
    vehicle_id  = db.Column(db.Integer, db.ForeignKey("vehicles.id"),  nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=True)

    # ── Financial ─────────────────────────────────────────────────────────────
    amount        = db.Column(db.Numeric(15, 2), nullable=False)
    amount_repaid = db.Column(db.Numeric(15, 2), default=0)

    # ── Details ───────────────────────────────────────────────────────────────
    reason       = db.Column(db.Text, nullable=False)
    expense_date = db.Column(db.Date, default=datetime.utcnow().date)
    owner        = db.Column(db.String(120), nullable=True)  # which owner paid

    # ── Status: outstanding | partially_paid | paid ───────────────────────────
    status       = db.Column(db.String(20), default="outstanding")

    notes        = db.Column(db.Text, nullable=True)
    is_archived  = db.Column(db.Boolean, default=False)
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by  = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def balance_due(self):
        return max(0.0, float(self.amount) - float(self.amount_repaid))

    def __repr__(self):
        return f"<Expense ₦{self.amount} driver={self.driver_id}>"
