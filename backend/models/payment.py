from datetime import datetime
from backend.extensions import db


class Payment(db.Model):
    __tablename__ = "payments"

    id = db.Column(db.Integer, primary_key=True)

    contract_id = db.Column(db.Integer, db.ForeignKey("contracts.id"), nullable=False)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=False)

    amount = db.Column(db.Numeric(15, 2), nullable=False)
    payment_date = db.Column(db.Date, default=datetime.utcnow().date)
    payment_time = db.Column(db.Time, nullable=True)

    sender = db.Column(db.String(120), nullable=True)
    receiver = db.Column(db.String(120), nullable=True)

    # Payment method: cash, pos, transfer
    payment_method = db.Column(db.String(20), default="cash")
    pos_terminal = db.Column(db.String(100), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    reference = db.Column(db.String(100), nullable=True)

    # Which week this payment contributes to (can span multiple)
    week_number = db.Column(db.Integer, nullable=True)

    notes = db.Column(db.Text, nullable=True)
    is_archived = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    recorded_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    def __repr__(self):
        return f"<Payment ₦{self.amount} driver={self.driver_id}>"
