"""
Administration blueprint — owner-only.
Handles: Business Settings, App Preferences, User Management.
"""
import os
from datetime import datetime
from functools import wraps

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, current_app)
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models.audit import AuditLog
from backend.models.user import User
from backend.models.settings import BusinessSettings, AppPreferences

admin_bp = Blueprint("admin", __name__)

LOGO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp", "svg"}

DATE_FORMAT_CHOICES = [
    ("%d %b %Y",  "14 Jul 2026"),
    ("%d/%m/%Y",  "14/07/2026"),
    ("%m/%d/%Y",  "07/14/2026"),
    ("%Y-%m-%d",  "2026-07-14"),
    ("%d-%m-%Y",  "14-07-2026"),
    ("%B %d, %Y", "July 14, 2026"),
]

TIMEZONE_CHOICES = [
    "Africa/Lagos",
    "Africa/Accra",
    "Africa/Nairobi",
    "Africa/Johannesburg",
    "Europe/London",
    "Europe/Paris",
    "America/New_York",
    "America/Chicago",
    "America/Los_Angeles",
    "UTC",
]


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if current_user.role != "owner":
            flash("Access restricted to owners.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated


def _log(action, entity_id=None, description=""):
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Admin",
        entity_id=entity_id or current_user.id,
        description=description or f"{action} by {current_user.username}",
        ip_address=request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
    ))


def _allowed_logo(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in LOGO_EXTENSIONS


# ── Overview / Business Settings ─────────────────────────────────────────────

@admin_bp.route("/")
@login_required
@owner_required
def index():
    biz   = BusinessSettings.get()
    prefs = AppPreferences.get()
    users = User.query.order_by(User.created_at).all()
    return render_template(
        "admin/index.html",
        biz=biz,
        prefs=prefs,
        users=users,
        date_format_choices=DATE_FORMAT_CHOICES,
        timezone_choices=TIMEZONE_CHOICES,
    )


@admin_bp.route("/business", methods=["POST"])
@login_required
@owner_required
def save_business():
    biz = BusinessSettings.get()

    name = (request.form.get("business_name") or "").strip()
    biz.business_name = name or biz.business_name
    biz.address       = (request.form.get("address") or "").strip() or None
    biz.phone         = (request.form.get("phone") or "").strip() or None
    biz.email         = (request.form.get("email") or "").strip() or None
    biz.website       = (request.form.get("website") or "").strip() or None
    biz.currency      = (request.form.get("currency") or "₦").strip()
    biz.timezone      = (request.form.get("timezone") or "Africa/Lagos").strip()
    biz.date_format   = (request.form.get("date_format") or "%d %b %Y").strip()

    logo_file = request.files.get("business_logo")
    if logo_file and logo_file.filename:
        if not _allowed_logo(logo_file.filename):
            flash("Logo must be a PNG, JPG, GIF, WEBP or SVG file.", "danger")
            return redirect(url_for("admin.index") + "#business")
        logo_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "logos")
        os.makedirs(logo_dir, exist_ok=True)
        filename = secure_filename(logo_file.filename)
        ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        stored_name = f"logo_{ts}_{filename}"
        logo_file.save(os.path.join(logo_dir, stored_name))
        biz.business_logo = stored_name

    _log("UPDATE_BUSINESS_SETTINGS", description=f"Business settings updated by {current_user.username}")
    db.session.commit()
    flash("Business settings saved successfully.", "success")
    return redirect(url_for("admin.index") + "#business")


# ── Application Preferences ───────────────────────────────────────────────────

@admin_bp.route("/preferences", methods=["POST"])
@login_required
@owner_required
def save_preferences():
    prefs = AppPreferences.get()

    try:
        size = int(request.form.get("pagination_size") or 20)
        prefs.pagination_size = max(5, min(100, size))
    except (ValueError, TypeError):
        pass

    fmt = request.form.get("default_report_format", "pdf")
    if fmt in ("pdf", "excel", "csv"):
        prefs.default_report_format = fmt

    theme = request.form.get("theme", "light")
    if theme in ("light", "dark"):
        prefs.theme = theme

    try:
        timeout = int(request.form.get("session_timeout") or 480)
        prefs.session_timeout = max(15, min(1440, timeout))
    except (ValueError, TypeError):
        pass

    _log("UPDATE_APP_PREFERENCES", description=f"App preferences updated by {current_user.username}")
    db.session.commit()

    # Apply session timeout to the running app immediately
    current_app.config["PERMANENT_SESSION_LIFETIME"] = prefs.session_timeout * 60

    flash("Application preferences saved successfully.", "success")
    return redirect(url_for("admin.index") + "#preferences")


# ── User Management ───────────────────────────────────────────────────────────

@admin_bp.route("/users/create", methods=["GET", "POST"])
@login_required
@owner_required
def create_user():
    if request.method == "POST":
        username     = (request.form.get("username") or "").strip()
        display_name = (request.form.get("display_name") or "").strip()
        email        = (request.form.get("email") or "").strip()
        password     = request.form.get("password") or ""
        confirm_pw   = request.form.get("confirm_password") or ""
        role         = request.form.get("role", "owner")

        if not username:
            flash("Username is required.", "danger")
            return redirect(url_for("admin.create_user"))
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return redirect(url_for("admin.create_user"))
        if password != confirm_pw:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("admin.create_user"))
        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return redirect(url_for("admin.create_user"))
        if email and User.query.filter(User.email == email).first():
            flash("Email already in use.", "danger")
            return redirect(url_for("admin.create_user"))
        if role not in ("owner", "developer"):
            role = "owner"

        user = User(
            username=username,
            display_name=display_name or None,
            email=email or None,
            role=role,
            is_active=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.flush()
        _log("CREATE_USER", entity_id=user.id,
             description=f"User '{username}' ({role}) created by {current_user.username}")
        db.session.commit()
        flash(f"User '{username}' created successfully.", "success")
        return redirect(url_for("admin.index") + "#users")

    return render_template("admin/user_form.html")


def _active_owner_count() -> int:
    return User.active_owner_count()


def _prevent_last_owner_change(user: User, action_desc: str):
    if user.role == "owner" and user.is_active and _active_owner_count() <= 1:
        flash(f"Cannot {action_desc}: this is the only active Owner account.", "danger")
        return False
    return True


@admin_bp.route("/users/<int:user_id>/toggle", methods=["POST"])
@login_required
@owner_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash("You cannot deactivate your own account.", "danger")
        return redirect(url_for("admin.index") + "#users")

    if not user.is_active and user.role == "owner":
        # Activating an owner is always allowed.
        pass
    elif user.role == "owner" and not _prevent_last_owner_change(user, "deactivate this Owner account"):
        return redirect(url_for("admin.index") + "#users")

    user.is_active = not user.is_active
    action = "REACTIVATE_USER" if user.is_active else "DEACTIVATE_USER"
    state = "activated" if user.is_active else "deactivated"
    _log(action, entity_id=user.id,
         description=f"User '{user.username}' {state} by {current_user.username}")
    db.session.commit()
    flash(f"User '{user.username}' {state}.", "success")
    return redirect(url_for("admin.index") + "#users")


@admin_bp.route("/users/<int:user_id>/reset-password", methods=["POST"])
@login_required
@owner_required
def reset_password(user_id):
    user       = User.query.get_or_404(user_id)
    new_pw     = request.form.get("new_password") or ""
    confirm_pw = request.form.get("confirm_password") or ""

    if len(new_pw) < 6:
        flash("New password must be at least 6 characters.", "danger")
        return redirect(url_for("admin.index") + "#users")
    if new_pw != confirm_pw:
        flash("Passwords do not match.", "danger")
        return redirect(url_for("admin.index") + "#users")

    user.set_password(new_pw)
    _log("RESET_PASSWORD", entity_id=user.id,
         description=f"Password reset for '{user.username}' by {current_user.username}")
    db.session.commit()
    flash(f"Password for '{user.username}' has been reset.", "success")
    return redirect(url_for("admin.index") + "#users")


@admin_bp.route("/users/<int:user_id>/role", methods=["POST"])
@login_required
@owner_required
def change_role(user_id):
    user     = User.query.get_or_404(user_id)
    new_role = request.form.get("role", "owner")

    if new_role not in ("owner", "developer"):
        flash("Invalid role.", "danger")
        return redirect(url_for("admin.index") + "#users")

    if user.role == "owner" and new_role != "owner":
        if not _prevent_last_owner_change(user, "change the role of this Owner account"):
            return redirect(url_for("admin.index") + "#users")

    old_role = user.role
    user.role = new_role
    _log("CHANGE_ROLE", entity_id=user.id,
         description=f"'{user.username}' role changed {old_role}→{new_role} by {current_user.username}")
    db.session.commit()
    flash(f"Role updated for '{user.username}'.", "success")
    return redirect(url_for("admin.index") + "#users")
