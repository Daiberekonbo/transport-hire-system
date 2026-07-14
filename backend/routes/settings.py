import os
from datetime import datetime

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models.audit import AuditLog
from backend.models.user import User

settings_bp = Blueprint("settings", __name__)

PHOTO_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_photo(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in PHOTO_EXTENSIONS


def _save_profile_photo(file_obj) -> str | None:
    """Save uploaded profile photo to static/uploads/profiles/; return stored filename or None."""
    if not file_obj or file_obj.filename == "":
        return None
    if not _allowed_photo(file_obj.filename):
        return None
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "profiles")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file_obj.filename)
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    stored_name = f"user{current_user.id}_{ts}_{filename}"
    file_obj.save(os.path.join(upload_dir, stored_name))
    return stored_name


def _log(action, description=""):
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Settings",
        entity_id=current_user.id,
        description=description or f"{action} by {current_user.username}",
        ip_address=request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
    ))


@settings_bp.route("/")
@login_required
def index():
    return render_template("settings/index.html")


@settings_bp.route("/profile", methods=["POST"])
@login_required
def update_profile():
    display_name = (request.form.get("display_name") or "").strip()
    username = (request.form.get("username") or "").strip()
    email = (request.form.get("email") or "").strip()

    if not username:
        flash("Username cannot be empty.", "danger")
        return redirect(url_for("settings.index"))

    existing = User.query.filter(User.username == username, User.id != current_user.id).first()
    if existing:
        flash("That username is already taken.", "danger")
        return redirect(url_for("settings.index"))

    if email:
        existing_email = User.query.filter(User.email == email, User.id != current_user.id).first()
        if existing_email:
            flash("That email is already in use.", "danger")
            return redirect(url_for("settings.index"))

    photo_file = request.files.get("profile_photo")
    if photo_file and photo_file.filename:
        if not _allowed_photo(photo_file.filename):
            flash("Profile picture must be a PNG, JPG, GIF or WEBP image.", "danger")
            return redirect(url_for("settings.index"))
        stored_name = _save_profile_photo(photo_file)
        if stored_name:
            current_user.profile_photo = stored_name

    old_username = current_user.username
    current_user.username = username
    current_user.display_name = display_name or None
    current_user.email = email or None

    _log("UPDATE_PROFILE", f"Profile updated by {old_username}")
    db.session.commit()
    flash("Profile updated successfully.", "success")
    return redirect(url_for("settings.index"))


@settings_bp.route("/change-password", methods=["POST"])
@login_required
def change_password():
    current_pw = request.form.get("current_password")
    new_pw = request.form.get("new_password")
    confirm_pw = request.form.get("confirm_password")

    if not current_user.check_password(current_pw):
        flash("Current password is incorrect.", "danger")
        return redirect(url_for("settings.index"))

    if new_pw != confirm_pw:
        flash("New passwords do not match.", "danger")
        return redirect(url_for("settings.index"))

    if len(new_pw) < 6:
        flash("Password must be at least 6 characters.", "danger")
        return redirect(url_for("settings.index"))

    current_user.set_password(new_pw)
    _log("CHANGE_PASSWORD", f"Password changed by {current_user.username}")
    db.session.commit()
    flash("Password changed successfully.", "success")
    return redirect(url_for("settings.index"))
