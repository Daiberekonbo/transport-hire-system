from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from backend.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    display_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(120), unique=True, nullable=True)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="owner")  # owner, developer
    is_active = db.Column(db.Boolean, default=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)

    @property
    def name(self):
        """Preferred display name, falling back to username."""
        return self.display_name or self.username

    audit_logs = db.relationship("AuditLog", backref="user", lazy="dynamic")
    recorded_expenses = db.relationship(
        "Expense", backref="recorder", lazy="dynamic",
        foreign_keys="Expense.recorded_by",
    )
    recorded_payments = db.relationship(
        "Payment", backref="recorder", lazy="dynamic",
        foreign_keys="Payment.recorded_by",
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def is_owner(self):
        return self.role == "owner"

    @property
    def is_developer(self):
        return self.role == "developer"

    @classmethod
    def active_owner_count(cls):
        return cls.query.filter_by(role="owner", is_active=True).count()

    def __repr__(self):
        return f"<User {self.username}>"
