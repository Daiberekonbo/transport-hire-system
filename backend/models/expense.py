from datetime import datetime
from backend.extensions import db


class Expense(db.Model):
    """Extra expenditure / loans advanced to drivers for vehicle repairs etc."""

    __tablename__ = "expenses"

    id = db.Column(db.Integer, primary_key=True)

    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("vehicles.id"), nullable=True)

    amount = db.Column(db.Numeric(15, 2), nullable=False)
    reason = db.Column(db.Text, nullable=False)
    expense_date = db.Column(db.Date, default=datetime.utcnow().date)
    owner = db.Column(db.String(120), nullable=True)  # which business owner paid

    # Status: outstanding, partially_paid, paid
    status = db.Column(db.String(20), default="outstanding")
    amount_repaid = db.Column(db.Numeric(15, 2), default=0)

    notes = db.Column(db.Text, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    @property
    def balance_due(self):
        return float(self.amount) - float(self.amount_repaid)

    def __repr__(self):
        return f"<Expense ₦{self.amount} driver={self.driver_id}>"
