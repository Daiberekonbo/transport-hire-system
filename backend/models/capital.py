"""
CapitalAdjustment — manual owner-only capital injections / withdrawals.

Everything else that feeds the Capital Management ledger (vehicle purchases,
payments, extra expenditures) is read live from the existing Vehicle,
Payment and Expense tables — nothing there is duplicated or migrated.
This table only stores the one genuinely new kind of transaction: a manual
adjustment made directly by the owner.

type
----
add       — owner injects additional capital into the business
withdraw  — owner withdraws capital from the business
"""

from datetime import datetime, date
from backend.extensions import db


class CapitalAdjustment(db.Model):
    __tablename__ = "capital_adjustments"

    id = db.Column(db.Integer, primary_key=True)

    type            = db.Column(db.String(20), nullable=False)   # add | withdraw
    amount          = db.Column(db.Numeric(15, 2), nullable=False)
    reason          = db.Column(db.Text, nullable=False)
    adjustment_date = db.Column(db.Date, default=date.today)

    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

    recorder = db.relationship("User", backref="capital_adjustments")

    @property
    def is_add(self):
        return self.type == "add"

    @property
    def signed_amount(self):
        amt = float(self.amount or 0)
        return amt if self.is_add else -amt

    @property
    def type_label(self):
        return "Capital Added" if self.is_add else "Capital Withdrawn"

    def __repr__(self):
        return f"<CapitalAdjustment {self.type} ₦{self.amount}>"
