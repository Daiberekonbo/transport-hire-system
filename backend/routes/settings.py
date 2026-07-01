from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from backend.extensions import db

settings_bp = Blueprint("settings", __name__)


@settings_bp.route("/")
@login_required
def index():
    return render_template("settings/index.html")


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
    db.session.commit()
    flash("Password changed successfully.", "success")
    return redirect(url_for("settings.index"))
