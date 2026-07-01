import sys
import platform
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.audit import AuditLog

developer_bp = Blueprint("developer", __name__)


def developer_required(f):
    from functools import wraps
    from flask import abort

    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "developer":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@developer_bp.route("/")
@login_required
@developer_required
def index():
    logs = AuditLog.query.order_by(AuditLog.created_at.desc()).limit(100).all()
    system_info = {
        "Python": sys.version,
        "Platform": platform.platform(),
        "SQLAlchemy": db.engine.url,
    }
    return render_template("developer/index.html", logs=logs, system_info=system_info)
