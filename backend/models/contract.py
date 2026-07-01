from datetime import datetime, date, timedelta
from backend.extensions import db


class Contract(db.Model):
    __tablename__ = "contracts"

    id = db.Column(db.Integer, primary_key=True)

    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=False)

    # Financial breakdown
    capital = db.Column(db.Numeric(15, 2), default=0)
    vehicle_cost = db.Column(db.Numeric(15, 2), default=0)
    extra_expenses = db.Column(db.Numeric(15, 2), default=0)
    service_costs = db.Column(db.Numeric(15, 2), default=0)
    total_payable = db.Column(db.Numeric(15, 2), default=0)
    weekly_amount = db.Column(db.Numeric(15, 2), default=0)

    # Duration
    years_agreed = db.Column(db.Integer, default=3)
    total_weeks = db.Column(db.Integer, default=156)  # years * 52

    # Progress
    weeks_completed = db.Column(db.Integer, default=0)
    start_date = db.Column(db.Date, default=date.today)
    expected_end_date = db.Column(db.Date, nullable=True)

    # Status: active, completed, terminated, archived
    status = db.Column(db.String(20), default="active")
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    payments = db.relationship("Payment", backref="contract", lazy="dynamic")

    @property
    def weeks_remaining(self):
        return max(0, self.total_weeks - self.weeks_completed)

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments)

    @property
    def outstanding_balance(self):
        return float(self.total_payable) - float(self.total_paid)

    @property
    def progress_percent(self):
        if self.total_weeks == 0:
            return 0
        return round((self.weeks_completed / self.total_weeks) * 100, 1)

    def set_duration(self, years):
        self.years_agreed = years
        self.total_weeks = years * 52
        if self.start_date:
            self.expected_end_date = self.start_date + timedelta(weeks=self.total_weeks)

    def __repr__(self):
        return f"<Contract driver={self.driver_id} vehicle={self.vehicle_id}>"
