from datetime import datetime
from backend.extensions import db


# ─── Action → display category mapping ────────────────────────────────────────
# Ordered by prefix specificity; first match wins. Used to derive a consistent
# badge label/color/icon for any action string logged across the app, without
# requiring every route to specify one explicitly.
_ACTION_CATEGORIES = [
    ("LOGIN",            "Login",   "success",   "bi-box-arrow-in-right"),
    ("LOGOUT",           "Logout",  "secondary", "bi-box-arrow-right"),
    ("RECORD_PAYMENT",   "Payment", "success",   "bi-cash-stack"),
    ("VOID_PAYMENT",     "Payment", "danger",    "bi-cash-stack"),
    ("RESTORE",          "Restore", "info",       "bi-arrow-counterclockwise"),
    ("REACTIVATE",       "Restore", "info",       "bi-arrow-counterclockwise"),
    ("ARCHIVE",          "Delete",  "danger",    "bi-archive-fill"),
    ("VOID",             "Delete",  "danger",    "bi-x-circle-fill"),
    ("DELETE",           "Delete",  "danger",    "bi-trash-fill"),
    ("WITHDRAW_CAPITAL", "Withdrawal", "danger", "bi-dash-circle-fill"),
    ("ADD_CAPITAL",      "Capital", "success",   "bi-bank2"),
    ("CREATE",           "Create",  "success",   "bi-plus-circle-fill"),
    ("ADD",              "Create",  "success",   "bi-plus-circle-fill"),
    ("EDIT",             "Update",  "primary",   "bi-pencil-fill"),
    ("UPDATE",           "Update",  "primary",   "bi-pencil-fill"),
    ("SUSPEND",          "Update",  "warning",   "bi-pause-circle-fill"),
    ("COMPLETE",         "Update",  "primary",   "bi-trophy-fill"),
    ("CHANGE_PASSWORD",  "System",  "dark",      "bi-shield-lock-fill"),
]


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

    # ── Display helpers (used by the Audit Log UI) ─────────────────────────
    def _category(self):
        act = (self.action or "").upper()
        for prefix, label, color, icon in _ACTION_CATEGORIES:
            if prefix in act:
                return label, color, icon
        return "System", "secondary", "bi-gear-fill"

    @property
    def action_label(self):
        return self._category()[0]

    @property
    def action_color(self):
        return self._category()[1]

    @property
    def action_icon(self):
        return self._category()[2]

    @property
    def module_label(self):
        return self.entity_type or "System"
