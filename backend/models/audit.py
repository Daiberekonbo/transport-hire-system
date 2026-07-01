from datetime import datetime
from backend.extensions import db


class AuditLog(db.Model):
    """Permanent record of every system action. Never deleted."""

    __tablename__ = "audit_logs"

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    action = db.Column(db.String(100), nullable=False)  # e.g. "CREATE_PAYMENT"
    entity_type = db.Column(db.String(50), nullable=True)  # e.g. "Payment"
    entity_id = db.Column(db.Integer, nullable=True)

    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    description = db.Column(db.Text, nullable=True)

    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AuditLog {self.action} by user={self.user_id}>"
