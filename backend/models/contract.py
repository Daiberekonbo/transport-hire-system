"""
Contract — core hire-purchase agreement.

Links one driver to one vehicle for an agreed number of years.
The driver pays a fixed weekly amount until the total_payable is cleared.

Status values
-------------
active      — currently running, payments being collected
suspended   — temporarily paused (e.g. vehicle off road)
inactive    — created but not yet activated, or paused indefinitely
completed   — driver has fully paid; vehicle released
archived    — administrative soft-delete of inactive/completed records

Financial model
---------------
capital              = vehicle_cost + service_costs + extra_expenses (editable)
total_payable        = what the driver must pay in total
total_extra_debt     = sum of extra expenditures added AFTER contract started
total_debt           = total_payable + total_extra_debt
total_paid           = sum of all non-archived payments
outstanding_balance  = total_debt − total_paid
weekly_amount        = total_payable / total_weeks
weeks_completed      = int(total_paid // weekly_amount)  — updated on every payment
"""

from datetime import datetime, date, timedelta
from backend.extensions import db


class Contract(db.Model):
    __tablename__ = "contracts"

    id         = db.Column(db.Integer, primary_key=True)
    driver_id  = db.Column(db.Integer, db.ForeignKey("drivers.id"),  nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)

    # ── Dates ─────────────────────────────────────────────────────────────────
    purchase_date     = db.Column(db.Date, nullable=True)      # when vehicle was purchased
    delivery_date     = db.Column(db.Date, nullable=True)      # when vehicle was delivered to driver
    start_date        = db.Column(db.Date, default=date.today) # contract agreement start
    expected_end_date = db.Column(db.Date, nullable=True)

    # ── Financial breakdown ───────────────────────────────────────────────────
    vehicle_cost   = db.Column(db.Numeric(15, 2), default=0)  # cost of the vehicle
    service_costs  = db.Column(db.Numeric(15, 2), default=0)  # initial servicing
    extra_expenses = db.Column(db.Numeric(15, 2), default=0)  # other startup costs
    capital        = db.Column(db.Numeric(15, 2), default=0)  # total capital invested (editable)
    total_payable  = db.Column(db.Numeric(15, 2), default=0)  # total the driver must pay

    # ── Duration ──────────────────────────────────────────────────────────────
    years_agreed   = db.Column(db.Integer, default=3)
    total_weeks    = db.Column(db.Integer, default=156)        # years * 52
    weekly_amount  = db.Column(db.Numeric(15, 2), default=0)   # total_payable / total_weeks

    # ── Progress ──────────────────────────────────────────────────────────────
    weeks_completed = db.Column(db.Integer, default=0)

    # ── Status & lifecycle ────────────────────────────────────────────────────
    status         = db.Column(db.String(20), default="active", nullable=False)
    notes          = db.Column(db.Text, nullable=True)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)
    date_completed = db.Column(db.DateTime, nullable=True)
    date_archived  = db.Column(db.DateTime, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    payments = db.relationship("Payment", backref="contract", lazy="dynamic")
    expenses = db.relationship(
        "Expense",
        primaryjoin="and_(Expense.contract_id == Contract.id, Expense.is_archived == False)",
        foreign_keys="Expense.contract_id",
        lazy="dynamic",
        overlaps="contract",
    )

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def total_paid(self):
        """Sum of all non-archived payments on this contract."""
        try:
            return sum(
                float(p.amount)
                for p in self.payments.filter_by(is_archived=False)
            )
        except Exception:
            return 0.0

    @property
    def total_extra_expenditure(self):
        """Sum of all extra expenditures (loans/advances) added after contract started."""
        try:
            return sum(float(e.amount) for e in self.expenses)
        except Exception:
            return 0.0

    @property
    def total_debt(self):
        """Original payable + all extra expenditures incurred."""
        return float(self.total_payable or 0) + self.total_extra_expenditure

    @property
    def outstanding_balance(self):
        """What the driver still owes: total debt minus what they have paid."""
        return max(0.0, self.total_debt - self.total_paid)

    @property
    def weeks_remaining(self):
        tw = int(self.total_weeks or 0)
        wc = int(self.weeks_completed or 0)
        return max(0, tw - wc)

    @property
    def progress_percent(self):
        tw = int(self.total_weeks or 0)
        wc = int(self.weeks_completed or 0)
        if tw == 0:
            return 0
        return round(min((wc / tw) * 100, 100), 1)

    @property
    def financial_progress_percent(self):
        """Progress based on ₦ paid vs total debt (more accurate when expenses added)."""
        td = self.total_debt
        if td == 0:
            return 0
        return round(min((self.total_paid / td) * 100, 100), 1)

    def recalculate_weeks(self):
        """Call after recording a payment to keep weeks_completed in sync."""
        wk = float(self.weekly_amount or 0)
        if wk > 0:
            self.weeks_completed = int(self.total_paid // wk)

    def set_duration(self, years):
        self.years_agreed  = years
        self.total_weeks   = years * 52
        if self.start_date:
            self.expected_end_date = self.start_date + timedelta(weeks=self.total_weeks)

    def __repr__(self):
        return f"<Contract #{self.id} driver={self.driver_id} vehicle={self.vehicle_id}>"
