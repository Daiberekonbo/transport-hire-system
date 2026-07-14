"""
BusinessSettings and AppPreferences — single-row configuration tables.

Both use a get() classmethod that creates the default row on first access,
so callers never need to handle None.
"""
from datetime import datetime
from backend.extensions import db


class BusinessSettings(db.Model):
    __tablename__ = "business_settings"

    id              = db.Column(db.Integer, primary_key=True)
    business_name   = db.Column(db.String(200), default="Transport Hire Management System")
    business_logo   = db.Column(db.String(255), nullable=True)
    address         = db.Column(db.Text, nullable=True)
    phone           = db.Column(db.String(200), nullable=True)
    email           = db.Column(db.String(120), nullable=True)
    website         = db.Column(db.String(200), nullable=True)
    currency        = db.Column(db.String(10),  default="₦")
    timezone        = db.Column(db.String(50),  default="Africa/Lagos")
    date_format     = db.Column(db.String(30),  default="%d %b %Y")
    updated_at      = db.Column(db.DateTime,    default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls):
        obj = cls.query.get(1)
        if not obj:
            obj = cls(id=1)
            db.session.add(obj)
            db.session.commit()
        return obj

    @property
    def display_name(self):
        return self.business_name or "Transport Hire Management System"

    @property
    def logo_url(self):
        """Return a URL-usable path fragment (relative to /static/) or None."""
        if self.business_logo:
            return f"uploads/logos/{self.business_logo}"
        return None

    def format_date(self, d):
        """Format a date/datetime using the configured date_format."""
        if not d:
            return ""
        fmt = self.date_format or "%d %b %Y"
        try:
            return d.strftime(fmt)
        except Exception:
            return str(d)


class AppPreferences(db.Model):
    __tablename__ = "app_preferences"

    id                    = db.Column(db.Integer, primary_key=True)
    pagination_size       = db.Column(db.Integer, default=20)
    default_report_format = db.Column(db.String(10), default="pdf")
    theme                 = db.Column(db.String(10), default="light")
    session_timeout       = db.Column(db.Integer, default=480)   # minutes
    updated_at            = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls):
        obj = cls.query.get(1)
        if not obj:
            obj = cls(id=1)
            db.session.add(obj)
            db.session.commit()
        return obj
