from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from backend.extensions import db
from backend.models.driver import Driver
from backend.models.audit import AuditLog

drivers_bp = Blueprint("drivers", __name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _log(action, driver, description=""):
    """Write a permanent audit entry for every driver mutation."""
    entry = AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Driver",
        entity_id=driver.id,
        description=description or f"{action} driver: {driver.full_name}",
    )
    db.session.add(entry)


def _populate(driver, form):
    """Copy all driver fields from a request form onto a Driver object."""
    driver.full_name        = form["full_name"].strip()
    driver.phone            = form["phone"].strip()
    driver.address          = form.get("address", "").strip() or None
    driver.national_id      = form.get("national_id", "").strip() or None
    driver.license_number   = form.get("license_number", "").strip() or None

    driver.nok_name         = form.get("nok_name", "").strip() or None
    driver.nok_phone        = form.get("nok_phone", "").strip() or None
    driver.nok_relationship = form.get("nok_relationship", "").strip() or None
    driver.nok_address      = form.get("nok_address", "").strip() or None

    driver.guarantor1_name    = form.get("guarantor1_name", "").strip() or None
    driver.guarantor1_phone   = form.get("guarantor1_phone", "").strip() or None
    driver.guarantor1_address = form.get("guarantor1_address", "").strip() or None

    driver.guarantor2_name    = form.get("guarantor2_name", "").strip() or None
    driver.guarantor2_phone   = form.get("guarantor2_phone", "").strip() or None
    driver.guarantor2_address = form.get("guarantor2_address", "").strip() or None

    driver.witness1_name    = form.get("witness1_name", "").strip() or None
    driver.witness1_phone   = form.get("witness1_phone", "").strip() or None
    driver.witness1_address = form.get("witness1_address", "").strip() or None

    driver.witness2_name    = form.get("witness2_name", "").strip() or None
    driver.witness2_phone   = form.get("witness2_phone", "").strip() or None
    driver.witness2_address = form.get("witness2_address", "").strip() or None

    driver.notes = form.get("notes", "").strip() or None


# ── routes ────────────────────────────────────────────────────────────────────

@drivers_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "active")
    page   = request.args.get("page", 1, type=int)

    query = Driver.query

    # Status filter
    if status and status != "all":
        query = query.filter(Driver.status == status)

    # Search across name and phone
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Driver.full_name.ilike(like),
                Driver.phone.ilike(like),
            )
        )

    drivers = query.order_by(Driver.date_registered.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    # Count by status for badge display
    counts = {
        "active":    Driver.query.filter_by(status="active").count(),
        "suspended": Driver.query.filter_by(status="suspended").count(),
        "archived":  Driver.query.filter_by(status="archived").count(),
    }

    return render_template(
        "drivers/index.html",
        drivers=drivers,
        search=search,
        status=status,
        counts=counts,
    )


@drivers_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        # Basic validation
        if not request.form.get("full_name", "").strip():
            flash("Full name is required.", "danger")
            return render_template("drivers/add.html", form=request.form)

        if not request.form.get("phone", "").strip():
            flash("Phone number is required.", "danger")
            return render_template("drivers/add.html", form=request.form)

        driver = Driver()
        _populate(driver, request.form)
        db.session.add(driver)
        db.session.flush()          # get the new id before logging
        _log("CREATE_DRIVER", driver)
        db.session.commit()

        flash(f"Driver '{driver.full_name}' registered successfully.", "success")
        return redirect(url_for("drivers.view", driver_id=driver.id))

    return render_template("drivers/add.html", form={})


@drivers_bp.route("/<int:driver_id>")
@login_required
def view(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    return render_template("drivers/view.html", driver=driver)


@drivers_bp.route("/<int:driver_id>/edit", methods=["GET", "POST"])
@login_required
def edit(driver_id):
    driver = Driver.query.get_or_404(driver_id)

    if driver.status == "archived":
        flash("Archived drivers cannot be edited.", "warning")
        return redirect(url_for("drivers.view", driver_id=driver_id))

    if request.method == "POST":
        if not request.form.get("full_name", "").strip():
            flash("Full name is required.", "danger")
            return render_template("drivers/edit.html", driver=driver, form=request.form)

        if not request.form.get("phone", "").strip():
            flash("Phone number is required.", "danger")
            return render_template("drivers/edit.html", driver=driver, form=request.form)

        old_status = driver.status
        _populate(driver, request.form)

        # Allow status change (active ↔ suspended) but not un-archiving here
        new_status = request.form.get("status", driver.status)
        if new_status in ("active", "suspended"):
            driver.status = new_status

        _log("EDIT_DRIVER", driver, f"Status: {old_status} → {driver.status}")
        db.session.commit()

        flash(f"Driver '{driver.full_name}' updated successfully.", "success")
        return redirect(url_for("drivers.view", driver_id=driver_id))

    return render_template("drivers/edit.html", driver=driver, form={})


@drivers_bp.route("/<int:driver_id>/archive", methods=["POST"])
@login_required
def archive(driver_id):
    """Soft-delete: sets status to 'archived' and records the date. Never deletes."""
    driver = Driver.query.get_or_404(driver_id)

    if driver.status == "archived":
        flash(f"'{driver.full_name}' is already archived.", "info")
        return redirect(url_for("drivers.view", driver_id=driver_id))

    driver.status = "archived"
    driver.date_archived = datetime.utcnow()
    _log("ARCHIVE_DRIVER", driver)
    db.session.commit()

    flash(f"Driver '{driver.full_name}' has been archived.", "warning")
    return redirect(url_for("drivers.index"))


@drivers_bp.route("/<int:driver_id>/restore", methods=["POST"])
@login_required
def restore(driver_id):
    """Restore an archived driver back to active."""
    driver = Driver.query.get_or_404(driver_id)

    if driver.status != "archived":
        flash(f"'{driver.full_name}' is not archived.", "info")
        return redirect(url_for("drivers.view", driver_id=driver_id))

    driver.status = "active"
    driver.date_archived = None
    _log("RESTORE_DRIVER", driver)
    db.session.commit()

    flash(f"Driver '{driver.full_name}' has been restored to active.", "success")
    return redirect(url_for("drivers.view", driver_id=driver_id))
