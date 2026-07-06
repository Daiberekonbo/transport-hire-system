"""
Expense — extra expenditure advanced to a driver against their contract.

These represent money paid by the owners on behalf of a driver:
vehicle repairs, accident damage, emergency loans, fines, parts, servicing, etc.

Every expense MUST be linked to a contract.  The contract's outstanding_balance
rises automatically via Contract.total_extra_expenditure (which sums all
non-archived expenses on that contract).

Expense number format
---------------------
  EXP-{YYYYMM}-{id:05d}   e.g.  EXP-202507-00017

Categories
----------
  vehicle_repairs  — mechanical / bodywork repairs
  accident_repairs — post-accident damage repair
  servicing        — routine maintenance / oil change
  fuel_advance     — advance on fuel costs
  driver_loan      — emergency cash loan to driver
  spare_parts      — replacement parts purchased
  insurance        — insurance premium or renewal
  fines            — government / traffic fines
  other            — any other approved expenditure
"""

from datetime import datetime
from backend.extensions import db


CATEGORIES = {
    "vehicle_repairs":  "Vehicle Repairs",
    "accident_repairs": "Accident Repairs",
    "servicing":        "Servicing",
    "fuel_advance":     "Fuel Advance",
    "driver_loan":      "Driver Loan",
    "spare_parts":      "Spare Parts",
    "insurance":        "Insurance",
    "fines":            "Fines",
    "other":            "Other",
}

CATEGORY_ICONS = {
    "vehicle_repairs":  "bi-wrench-adjustable-circle",
    "accident_repairs": "bi-shield-exclamation",
    "servicing":        "bi-gear-fill",
    "fuel_advance":     "bi-fuel-pump-fill",
    "driver_loan":      "bi-cash-coin",
    "spare_parts":      "bi-box-seam-fill",
    "insurance":        "bi-shield-check-fill",
    "fines":            "bi-exclamation-triangle-fill",
    "other":            "bi-three-dots-vertical",
}

CATEGORY_COLORS = {
    "vehicle_repairs":  "warning",
    "accident_repairs": "danger",
    "servicing":        "info",
    "fuel_advance":     "primary",
    "driver_loan":      "purple",
    "spare_parts":      "secondary",
    "insurance":        "success",
    "fines":            "danger",
    "other":            "secondary",
}


class Expense(db.Model):
    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)

    # ── Links ─────────────────────────────────────────────────────────────────
    driver_id   = db.Column(db.Integer, db.ForeignKey("drivers.id"),   nullable=False)
    vehicle_id  = db.Column(db.Integer, db.ForeignKey("vehicles.id"),  nullable=True)
    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=True)

    # ── Reference number ──────────────────────────────────────────────────────
    expense_number = db.Column(db.String(30), nullable=True, unique=True)

    # ── Core details ──────────────────────────────────────────────────────────
    title       = db.Column(db.String(160), nullable=False, default="")
    category    = db.Column(db.String(40),  nullable=False, default="other")
    description = db.Column(db.Text,        nullable=True)

    # legacy field — kept for backward compatibility with old records
    reason = db.Column(db.Text, nullable=True)

    # ── Financial ─────────────────────────────────────────────────────────────
    amount        = db.Column(db.Numeric(15, 2), nullable=False)
    amount_repaid = db.Column(db.Numeric(15, 2), default=0)

    # ── Date / time ───────────────────────────────────────────────────────────
    expense_date = db.Column(db.Date,    default=datetime.utcnow().date)
    expense_time = db.Column(db.Time,    nullable=True)

    # ── Authorisation ─────────────────────────────────────────────────────────
    approved_by = db.Column(db.String(120), nullable=True)
    owner       = db.Column(db.String(120), nullable=True)   # legacy: who paid

    # ── Supporting document ───────────────────────────────────────────────────
    receipt_file = db.Column(db.String(255), nullable=True)

    # ── Status: outstanding | partially_paid | paid ───────────────────────────
    status = db.Column(db.String(20), default="outstanding")

    # ── Notes ─────────────────────────────────────────────────────────────────
    notes = db.Column(db.Text, nullable=True)

    # ── Meta ──────────────────────────────────────────────────────────────────
    is_archived = db.Column(db.Boolean,  default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer,  db.ForeignKey("users.id"), nullable=True)

    # ── Computed properties ────────────────────────────────────────────────────

    @property
    def category_label(self):
        return CATEGORIES.get(self.category, self.category or "Other")

    @property
    def category_icon(self):
        return CATEGORY_ICONS.get(self.category, "bi-three-dots-vertical")

    @property
    def category_color(self):
        return CATEGORY_COLORS.get(self.category, "secondary")

    @property
    def balance_due(self):
        return max(0.0, float(self.amount or 0) - float(self.amount_repaid or 0))

    @property
    def display_title(self):
        return self.title or self.reason or "Expenditure"

    @property
    def display_description(self):
        return self.description or self.reason or ""

    def __repr__(self):
        return f"<Expense #{self.id} ₦{self.amount} [{self.category}]>"
