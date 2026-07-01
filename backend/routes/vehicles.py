"""
Vehicle Management Routes
=========================
Provides full CRUD for fleet vehicles:

  GET  /vehicles/                 — list with search, status tabs, pagination
  GET  /vehicles/add              — add form
  POST /vehicles/add              — create vehicle + write "registered" timeline event
  GET  /vehicles/<id>             — vehicle profile + full timeline
  GET  /vehicles/<id>/edit        — pre-filled edit form
  POST /vehicles/<id>/edit        — update vehicle; log status changes
  POST /vehicles/<id>/archive     — soft-archive vehicle
  POST /vehicles/<id>/restore     — restore archived vehicle
  POST /vehicles/<id>/events/add  — manually add a timeline note / event

Business rules enforced here
-----------------------------
- Archived vehicles cannot be edited.
- A vehicle already under an active contract cannot be manually set to
  "available" via edit (the contract module owns that transition).
- Archiving a vehicle with an active contract is blocked.
- Multiple drivers cannot be assigned to one vehicle (enforced when
  the Contract module is built; placeholder check exists here).
"""

from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from backend.extensions import db
from backend.models.vehicle import Vehicle
from backend.models.vehicle_event import VehicleEvent
from backend.models.audit import AuditLog

vehicles_bp = Blueprint("vehicles", __name__)


# ── helpers ───────────────────────────────────────────────────────────────────

def _log(action: str, vehicle: Vehicle, description: str = ""):
    """Write a permanent AuditLog entry for every vehicle mutation."""
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Vehicle",
        entity_id=vehicle.id,
        description=description or f"{action}: {vehicle.vehicle_number}",
    ))


def _event(vehicle: Vehicle, event_type: str, title: str, description: str = ""):
    """Append a VehicleEvent to the vehicle's timeline."""
    db.session.add(VehicleEvent(
        vehicle_id=vehicle.id,
        event_type=event_type,
        title=title,
        description=description or None,
        event_date=datetime.utcnow(),
        created_by=current_user.username,
    ))


def _populate(vehicle: Vehicle, form):
    """
    Map every form field onto the Vehicle object.
    Called for both ADD and EDIT so field handling stays in one place.
    """
    vehicle.vehicle_number = form["vehicle_number"].strip()
    vehicle.reg_number     = form.get("reg_number", "").strip() or None
    vehicle.engine_number  = form.get("engine_number", "").strip() or None
    vehicle.chassis_number = form.get("chassis_number", "").strip() or None

    vehicle.manufacturer   = form.get("manufacturer", "").strip() or None
    vehicle.model          = form.get("model", "").strip() or None

    _year = form.get("year", "").strip()
    vehicle.year = int(_year) if _year.isdigit() else None

    vehicle.color = form.get("color", "").strip() or None

    _price = form.get("purchase_price", "").strip().replace(",", "")
    vehicle.purchase_price = float(_price) if _price else 0

    vehicle.purchase_date  = _parse_date(form.get("purchase_date"))
    vehicle.delivery_date  = _parse_date(form.get("delivery_date"))

    _mileage = form.get("current_mileage", "").strip()
    vehicle.current_mileage = int(_mileage) if _mileage.isdigit() else None

    vehicle.insurance_expiry       = _parse_date(form.get("insurance_expiry"))
    vehicle.road_worthiness_expiry = _parse_date(form.get("road_worthiness_expiry"))

    vehicle.notes = form.get("notes", "").strip() or None


def _parse_date(value):
    """Convert 'YYYY-MM-DD' string → date object, or return None."""
    if not value:
        return None
    try:
        from datetime import date
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


# ── list ──────────────────────────────────────────────────────────────────────

@vehicles_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "").strip()
    status = request.args.get("status", "all")
    page   = request.args.get("page", 1, type=int)

    query = Vehicle.query

    if status and status != "all":
        query = query.filter(Vehicle.status == status)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Vehicle.vehicle_number.ilike(like),
                Vehicle.reg_number.ilike(like),
                Vehicle.manufacturer.ilike(like),
                Vehicle.model.ilike(like),
                Vehicle.color.ilike(like),
            )
        )

    vehicles = query.order_by(Vehicle.date_registered.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    counts = {
        "available":   Vehicle.query.filter_by(status="available").count(),
        "assigned":    Vehicle.query.filter_by(status="assigned").count(),
        "maintenance": Vehicle.query.filter_by(status="maintenance").count(),
        "archived":    Vehicle.query.filter_by(status="archived").count(),
    }

    return render_template(
        "vehicles/index.html",
        vehicles=vehicles,
        search=search,
        status=status,
        counts=counts,
    )


# ── add ───────────────────────────────────────────────────────────────────────

@vehicles_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        plate = request.form.get("vehicle_number", "").strip()
        if not plate:
            flash("Plate / fleet number is required.", "danger")
            return render_template("vehicles/add.html", form=request.form)

        # Duplicate check
        if Vehicle.query.filter_by(vehicle_number=plate).first():
            flash(f"A vehicle with plate number '{plate}' already exists.", "danger")
            return render_template("vehicles/add.html", form=request.form)

        vehicle = Vehicle()
        _populate(vehicle, request.form)
        vehicle.status = "available"
        db.session.add(vehicle)
        db.session.flush()          # get vehicle.id before writing events

        _event(vehicle, "registered",
               f"Vehicle {vehicle.vehicle_number} registered in the system",
               f"Added by {current_user.username}.")
        _log("ADD_VEHICLE", vehicle)
        db.session.commit()

        flash(f"Vehicle '{vehicle.vehicle_number}' added successfully.", "success")
        return redirect(url_for("vehicles.view", vehicle_id=vehicle.id))

    return render_template("vehicles/add.html", form={})


# ── view ──────────────────────────────────────────────────────────────────────

@vehicles_bp.route("/<int:vehicle_id>")
@login_required
def view(vehicle_id):
    from datetime import date
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    timeline = vehicle.events.order_by(VehicleEvent.event_date.desc()).limit(100).all()
    return render_template(
        "vehicles/view.html",
        vehicle=vehicle,
        timeline=timeline,
        today=date.today(),
    )


# ── edit ──────────────────────────────────────────────────────────────────────

@vehicles_bp.route("/<int:vehicle_id>/edit", methods=["GET", "POST"])
@login_required
def edit(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if vehicle.status == "archived":
        flash("Archived vehicles cannot be edited. Restore the vehicle first.", "warning")
        return redirect(url_for("vehicles.view", vehicle_id=vehicle_id))

    if request.method == "POST":
        plate = request.form.get("vehicle_number", "").strip()
        if not plate:
            flash("Plate / fleet number is required.", "danger")
            return render_template("vehicles/edit.html", vehicle=vehicle, form=request.form)

        # Duplicate check (exclude self)
        existing = Vehicle.query.filter_by(vehicle_number=plate).first()
        if existing and existing.id != vehicle.id:
            flash(f"Another vehicle already uses plate number '{plate}'.", "danger")
            return render_template("vehicles/edit.html", vehicle=vehicle, form=request.form)

        old_status = vehicle.status
        _populate(vehicle, request.form)

        # Status change — restricted transitions
        new_status = request.form.get("status", old_status)
        allowed_statuses = {"available", "assigned", "maintenance"}

        # Cannot manually un-assign a vehicle that has an active contract
        if old_status == "assigned" and new_status != "assigned":
            if vehicle.active_contract:
                flash(
                    "This vehicle has an active hire-purchase contract. "
                    "The status cannot be changed manually — close the contract first.",
                    "warning",
                )
                return render_template("vehicles/edit.html", vehicle=vehicle, form=request.form)

        if new_status in allowed_statuses:
            vehicle.status = new_status

        if old_status != vehicle.status:
            _event(
                vehicle, "status_change",
                f"Status changed: {old_status} → {vehicle.status}",
                f"Changed by {current_user.username}.",
            )

        _log("EDIT_VEHICLE", vehicle, f"Status: {old_status} → {vehicle.status}")
        db.session.commit()

        flash(f"Vehicle '{vehicle.vehicle_number}' updated successfully.", "success")
        return redirect(url_for("vehicles.view", vehicle_id=vehicle_id))

    return render_template("vehicles/edit.html", vehicle=vehicle, form={})


# ── archive ───────────────────────────────────────────────────────────────────

@vehicles_bp.route("/<int:vehicle_id>/archive", methods=["POST"])
@login_required
def archive(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if vehicle.status == "archived":
        flash(f"'{vehicle.vehicle_number}' is already archived.", "info")
        return redirect(url_for("vehicles.view", vehicle_id=vehicle_id))

    if vehicle.active_contract:
        flash(
            f"'{vehicle.vehicle_number}' has an active hire-purchase contract. "
            "Close the contract before archiving this vehicle.",
            "danger",
        )
        return redirect(url_for("vehicles.view", vehicle_id=vehicle_id))

    vehicle.status = "archived"
    vehicle.date_archived = datetime.utcnow()

    _event(vehicle, "archived",
           f"Vehicle {vehicle.vehicle_number} archived",
           f"Archived by {current_user.username}.")
    _log("ARCHIVE_VEHICLE", vehicle)
    db.session.commit()

    flash(f"Vehicle '{vehicle.vehicle_number}' has been archived.", "warning")
    return redirect(url_for("vehicles.index"))


# ── restore ───────────────────────────────────────────────────────────────────

@vehicles_bp.route("/<int:vehicle_id>/restore", methods=["POST"])
@login_required
def restore(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    if vehicle.status != "archived":
        flash(f"'{vehicle.vehicle_number}' is not archived.", "info")
        return redirect(url_for("vehicles.view", vehicle_id=vehicle_id))

    vehicle.status = "available"
    vehicle.date_archived = None

    _event(vehicle, "restored",
           f"Vehicle {vehicle.vehicle_number} restored to fleet",
           f"Restored by {current_user.username}.")
    _log("RESTORE_VEHICLE", vehicle)
    db.session.commit()

    flash(f"Vehicle '{vehicle.vehicle_number}' has been restored to the fleet.", "success")
    return redirect(url_for("vehicles.view", vehicle_id=vehicle_id))


# ── add manual timeline event / note ─────────────────────────────────────────

@vehicles_bp.route("/<int:vehicle_id>/events/add", methods=["POST"])
@login_required
def add_event(vehicle_id):
    """Allow staff to manually append a maintenance record, repair note, or any event."""
    vehicle = Vehicle.query.get_or_404(vehicle_id)

    event_type  = request.form.get("event_type", "note")
    title       = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    event_date_raw = request.form.get("event_date", "").strip()

    if not title:
        flash("Event title is required.", "danger")
        return redirect(url_for("vehicles.view", vehicle_id=vehicle_id))

    event_date = _parse_date(event_date_raw)

    db.session.add(VehicleEvent(
        vehicle_id=vehicle.id,
        event_type=event_type,
        title=title,
        description=description or None,
        event_date=event_date or datetime.utcnow(),
        created_by=current_user.username,
    ))

    # Auto-update status for maintenance events
    if event_type == "maintenance_start" and vehicle.status == "available":
        vehicle.status = "maintenance"
        flash("Vehicle status updated to Maintenance.", "info")
    elif event_type == "maintenance_end" and vehicle.status == "maintenance":
        vehicle.status = "available"
        flash("Vehicle status updated to Available.", "info")

    db.session.commit()
    flash("Event recorded on the vehicle timeline.", "success")
    return redirect(url_for("vehicles.view", vehicle_id=vehicle_id) + "#timeline")
