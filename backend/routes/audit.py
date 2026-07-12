"""
Audit Log Routes
=================

GET /audit-log/    — searchable, filterable, paginated audit trail

Access
------
Owners only can view the full audit trail (developers already have their own
system diagnostics page under /developer). Audit logs are permanent and there
is intentionally no edit/delete route for them.
"""

from datetime import datetime
from functools import wraps

from flask import Blueprint, render_template, request, abort
from flask_login import login_required, current_user
from sqlalchemy import or_

from backend.models.audit import AuditLog
from backend.models.user import User

audit_bp = Blueprint("audit", __name__)


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "owner":
            abort(403)
        return f(*args, **kwargs)
    return decorated


@audit_bp.route("/")
@login_required
@owner_required
def index():
    search      = request.args.get("q", "").strip()
    user_filter = request.args.get("user_id", "")
    module_filter = request.args.get("module", "")
    action_filter = request.args.get("action", "")
    date_from_s = request.args.get("date_from", "")
    date_to_s   = request.args.get("date_to", "")
    page        = request.args.get("page", 1, type=int)

    query = AuditLog.query.outerjoin(User, AuditLog.user_id == User.id)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                AuditLog.description.ilike(like),
                AuditLog.action.ilike(like),
                User.username.ilike(like),
            )
        )

    if user_filter:
        query = query.filter(AuditLog.user_id == user_filter)

    if module_filter:
        query = query.filter(AuditLog.entity_type == module_filter)

    if action_filter:
        query = query.filter(AuditLog.action == action_filter)

    if date_from_s:
        try:
            df = datetime.strptime(date_from_s, "%Y-%m-%d")
            query = query.filter(AuditLog.created_at >= df)
        except ValueError:
            pass

    if date_to_s:
        try:
            dt = datetime.strptime(date_to_s, "%Y-%m-%d")
            dt = dt.replace(hour=23, minute=59, second=59)
            query = query.filter(AuditLog.created_at <= dt)
        except ValueError:
            pass

    logs = query.order_by(AuditLog.created_at.desc()).paginate(
        page=page, per_page=30, error_out=False
    )

    # Distinct filter options, derived from the actual data present.
    users   = User.query.order_by(User.username).all()
    modules = sorted({
        row[0] for row in AuditLog.query.with_entities(AuditLog.entity_type).distinct()
        if row[0]
    })
    actions = sorted({
        row[0] for row in AuditLog.query.with_entities(AuditLog.action).distinct()
        if row[0]
    })

    return render_template(
        "audit/index.html",
        logs=logs,
        users=users,
        modules=modules,
        actions=actions,
        search=search,
        user_filter=user_filter,
        module_filter=module_filter,
        action_filter=action_filter,
        date_from_s=date_from_s,
        date_to_s=date_to_s,
    )
