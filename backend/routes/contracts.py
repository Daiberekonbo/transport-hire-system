"""
Hire-Purchase Contract Management Routes
=========================================

Routes
------
GET  /contracts/                      — list (all statuses via tabs)
GET  /contracts/add                   — create form
POST /contracts/add                   — create contract
GET  /contracts/<id>                  — contract detail + timeline
GET  /contracts/<id>/edit             — edit form
POST /contracts/<id>/edit             — save edits
POST /contracts/<id>/complete         — mark as completed; releases vehicle
POST /contracts/<id>/suspend          — suspend active contract
POST /contracts/<id>/reactivate       — reactivate suspended/inactive
POST /contracts/<id>/archive          — soft-archive inactive/completed contract

Business rules enforced here
-----------------------------
• A vehicle can only have ONE active contract at a time (hard rule).
• A driver can only have ONE active contract at a time UNLESS the user
  explicitly checks the override checkbox on the create form.
• Completing a contract automatically sets the vehicle status → available
  and appends a 'contract_completed' + 'returned' VehicleEvent.
• Nothing is ever permanently deleted. Completed contracts remain accessible
  under the "Completed" status tab.
• Every mutation is recorded in AuditLog.
"""

from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from sqlalchemy import or_
from backend.extensions import db
from backend.models.contract import Contract
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.models.vehicle_event import VehicleEvent
from backend.models.payment import Payment
from backend.models.expense import Expense
from backend.models.audit import AuditLog

contracts_bp = Blueprint("contracts", __name__)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _f(val, default=0.0):
    """Parse a money string → float."""
    try:
        return float(str(val).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _i(val, default=0):
    """Parse an int string → int."""
    try:
        return int(str(val).strip())
    except (TypeError, ValueError):
        return default


def _d(val):
    """Parse 'YYYY-MM-DD' → date object, or None."""
    if not val:
        return None
    try:
        return datetime.strptime(str(val).strip(), "%Y-%m-%d").date()
    except ValueError:
        return None


def _log(action: str, contract: Contract, description: str = ""):
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Contract",
        entity_id=contract.id,
        description=description or f"{action}: contract #{contract.id}",
        ip_address=request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
    ))


def _vehicle_event(vehicle: Vehicle, event_type: str, title: str, description: str = ""):
    db.session.add(VehicleEvent(
        vehicle_id=vehicle.id,
        event_type=event_type,
        title=title,
        description=description or None,
        event_date=datetime.utcnow(),
        created_by=current_user.username,
    ))


def _populate(contract: Contract, form):
    """Map form fields onto a Contract object. Called for both ADD and EDIT."""
    contract.vehicle_cost   = _f(form.get("vehicle_cost"))
    contract.service_costs  = _f(form.get("service_costs"))
    contract.extra_expenses = _f(form.get("extra_expenses"))

    # capital: auto-calc or use the manually entered value
    auto_capital = contract.vehicle_cost + contract.service_costs + contract.extra_expenses
    entered_capital = _f(form.get("capital"), default=-1)
    contract.capital = entered_capital if entered_capital >= 0 else auto_capital

    contract.total_payable  = _f(form.get("total_payable"))
    contract.years_agreed   = _i(form.get("years_agreed", 3), default=3)
    contract.total_weeks    = contract.years_agreed * 52

    wk = float(contract.weekly_amount or 0)
    if float(contract.total_payable) > 0 and contract.total_weeks > 0:
        contract.weekly_amount = float(contract.total_payable) / contract.total_weeks
    elif wk > 0:
        contract.weekly_amount = wk

    contract.start_date    = _d(form.get("start_date")) or date.today()
    contract.purchase_date = _d(form.get("purchase_date"))
    contract.delivery_date = _d(form.get("delivery_date"))
    contract.expected_end_date = (
        contract.start_date + timedelta(weeks=contract.total_weeks)
    )
    contract.notes = form.get("notes", "").strip() or None


def _build_timeline(contract: Contract):
    """
    Merge contract milestones, payments, and expenses into a single
    chronological list (newest first) for the detail page.
    """
    events = []

    # ── Static milestones ────────────────────────────────────────────────────
    events.append({
        "date": contract.created_at,
        "type": "contract_created",
        "icon": "bi-file-earmark-check-fill text-primary",
        "title": "Contract created",
        "description": (
            f"Hire-purchase agreement between {contract.driver.full_name} "
            f"and vehicle {contract.vehicle.vehicle_number}. "
            f"Weekly payment: ₦{float(contract.weekly_amount):,.0f} "
            f"over {contract.total_weeks} weeks."
        ),
        "amount": None,
    })

    if contract.purchase_date:
        events.append({
            "date": datetime.combine(contract.purchase_date, datetime.min.time()),
            "type": "purchase",
            "icon": "bi-cart-check-fill text-success",
            "title": f"Vehicle purchased — {contract.vehicle.vehicle_number}",
            "description": (
                f"Purchase price: ₦{float(contract.vehicle_cost):,.0f}"
                if contract.vehicle_cost else ""
            ),
            "amount": float(contract.vehicle_cost) if contract.vehicle_cost else None,
        })

    if contract.delivery_date:
        events.append({
            "date": datetime.combine(contract.delivery_date, datetime.min.time()),
            "type": "delivery",
            "icon": "bi-truck-front-fill text-info",
            "title": f"Vehicle delivered to {contract.driver.full_name}",
            "description": f"Vehicle {contract.vehicle.vehicle_number} handed over to driver.",
            "amount": None,
        })

    # ── Payments ─────────────────────────────────────────────────────────────
    for p in contract.payments.filter_by(is_archived=False).all():
        events.append({
            "date": datetime.combine(p.payment_date, datetime.min.time())
            if not hasattr(p.payment_date, "hour")
            else p.payment_date,
            "type": "payment",
            "icon": "bi-cash-stack text-success",
            "title": f"Payment received — ₦{float(p.amount):,.0f}",
            "description": (
                f"Method: {p.payment_method.upper() if p.payment_method else 'Cash'}"
                + (f" · Ref: {p.reference}" if p.reference else "")
                + (f" · {p.notes}" if p.notes else "")
            ),
            "amount": float(p.amount),
        })

    # ── Extra expenditures ────────────────────────────────────────────────────
    for e in Expense.query.filter_by(contract_id=contract.id, is_archived=False).all():
        events.append({
            "date": datetime.combine(e.expense_date, datetime.min.time())
            if not hasattr(e.expense_date, "hour")
            else e.expense_date,
            "type": "expense",
            "icon": "bi-exclamation-triangle-fill text-danger",
            "title": f"Extra expenditure — ₦{float(e.amount):,.0f}",
            "description": e.reason + (f" · {e.notes}" if e.notes else ""),
            "amount": float(e.amount),
        })

    # ── Completion / archive milestones ───────────────────────────────────────
    if contract.date_completed:
        events.append({
            "date": contract.date_completed,
            "type": "completed",
            "icon": "bi-trophy-fill text-warning",
            "title": "Contract completed",
            "description": (
                f"{contract.driver.full_name} has completed all hire-purchase payments. "
                f"Vehicle {contract.vehicle.vehicle_number} fully transferred."
            ),
            "amount": None,
        })

    if contract.date_archived:
        events.append({
            "date": contract.date_archived,
            "type": "archived",
            "icon": "bi-archive-fill text-secondary",
            "title": "Contract archived",
            "description": "Record archived for permanent preservation.",
            "amount": None,
        })

    events.sort(key=lambda x: x["date"], reverse=True)
    return events


# ─── routes ───────────────────────────────────────────────────────────────────

@contracts_bp.route("/")
@login_required
def index():
    status  = request.args.get("status", "active")
    search  = request.args.get("q", "").strip()
    page    = request.args.get("page", 1, type=int)

    query = (
        Contract.query
        .join(Driver,  Contract.driver_id  == Driver.id)
        .join(Vehicle, Contract.vehicle_id == Vehicle.id)
    )

    if status and status != "all":
        query = query.filter(Contract.status == status)

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Driver.full_name.ilike(like),
                Vehicle.vehicle_number.ilike(like),
                Vehicle.model.ilike(like),
            )
        )

    contracts = query.order_by(Contract.created_at.desc()).paginate(
        page=page, per_page=15, error_out=False
    )

    counts = {
        "active":    Contract.query.filter_by(status="active").count(),
        "suspended": Contract.query.filter_by(status="suspended").count(),
        "inactive":  Contract.query.filter_by(status="inactive").count(),
        "completed": Contract.query.filter_by(status="completed").count(),
        "archived":  Contract.query.filter_by(status="archived").count(),
    }

    return render_template(
        "contracts/index.html",
        contracts=contracts,
        status=status,
        search=search,
        counts=counts,
    )


@contracts_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    drivers  = (Driver.query
                .filter(Driver.status.in_(["active", "suspended"]))
                .order_by(Driver.full_name).all())
    vehicles = (Vehicle.query
                .filter(Vehicle.status.in_(["available", "maintenance"]))
                .order_by(Vehicle.vehicle_number).all())

    if request.method == "POST":
        driver_id  = request.form.get("driver_id",  type=int)
        vehicle_id = request.form.get("vehicle_id", type=int)
        override   = request.form.get("override_driver_check") == "on"

        if not driver_id or not vehicle_id:
            flash("Driver and vehicle are both required.", "danger")
            return render_template("contracts/add.html",
                                   drivers=drivers, vehicles=vehicles,
                                   form=request.form, today=date.today())

        driver  = Driver.query.get_or_404(driver_id)
        vehicle = Vehicle.query.get_or_404(vehicle_id)

        # ── Business rule checks ──────────────────────────────────────────────
        existing_driver = Contract.query.filter_by(
            driver_id=driver_id, status="active"
        ).first()
        if existing_driver and not override:
            flash(
                f"'{driver.full_name}' already has an active contract "
                f"(Contract #{existing_driver.id}). "
                "Tick 'Allow override' to proceed anyway.",
                "danger",
            )
            return render_template("contracts/add.html",
                                   drivers=drivers, vehicles=vehicles,
                                   form=request.form, today=date.today(),
                                   show_override=True)

        existing_vehicle = Contract.query.filter_by(
            vehicle_id=vehicle_id, status="active"
        ).first()
        if existing_vehicle:
            flash(
                f"Vehicle '{vehicle.vehicle_number}' already has an active "
                f"contract (Contract #{existing_vehicle.id}). "
                "A vehicle can only hold one active contract.",
                "danger",
            )
            return render_template("contracts/add.html",
                                   drivers=drivers, vehicles=vehicles,
                                   form=request.form, today=date.today())

        # ── Validate financials ───────────────────────────────────────────────
        total_payable = _f(request.form.get("total_payable"))
        years_agreed  = _i(request.form.get("years_agreed", 3), default=3)
        if total_payable <= 0:
            flash("Total amount payable must be greater than zero.", "danger")
            return render_template("contracts/add.html",
                                   drivers=drivers, vehicles=vehicles,
                                   form=request.form, today=date.today())
        if years_agreed <= 0:
            flash("Number of years must be at least 1.", "danger")
            return render_template("contracts/add.html",
                                   drivers=drivers, vehicles=vehicles,
                                   form=request.form, today=date.today())

        # ── Create contract ───────────────────────────────────────────────────
        contract = Contract(driver_id=driver_id, vehicle_id=vehicle_id, status="active")
        _populate(contract, request.form)

        db.session.add(contract)
        db.session.flush()  # get contract.id before logging

        # Update vehicle status to 'assigned'
        vehicle.status = "assigned"
        _vehicle_event(
            vehicle, "assigned",
            f"Assigned to {driver.full_name} — Contract #{contract.id}",
            f"Weekly payment: ₦{float(contract.weekly_amount):,.2f} "
            f"over {contract.total_weeks} weeks.",
        )

        _log("CREATE_CONTRACT", contract,
             f"Contract for {driver.full_name} on {vehicle.vehicle_number}. "
             f"Total payable: ₦{float(contract.total_payable):,.0f}")
        db.session.commit()

        flash(
            f"Contract #{contract.id} created for {driver.full_name} / "
            f"{vehicle.vehicle_number}.",
            "success",
        )
        return redirect(url_for("contracts.view", contract_id=contract.id))

    return render_template(
        "contracts/add.html",
        drivers=drivers,
        vehicles=vehicles,
        form={},
        today=date.today(),
        show_override=False,
    )


@contracts_bp.route("/<int:contract_id>")
@login_required
def view(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    timeline = _build_timeline(contract)
    return render_template(
        "contracts/view.html",
        contract=contract,
        timeline=timeline,
        today=date.today(),
    )


@contracts_bp.route("/<int:contract_id>/edit", methods=["GET", "POST"])
@login_required
def edit(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    if contract.status in ("completed", "archived"):
        flash("Completed or archived contracts cannot be edited.", "warning")
        return redirect(url_for("contracts.view", contract_id=contract_id))

    if request.method == "POST":
        total_payable = _f(request.form.get("total_payable"))
        years_agreed  = _i(request.form.get("years_agreed", 3))
        if total_payable <= 0:
            flash("Total amount payable must be greater than zero.", "danger")
            return render_template("contracts/edit.html", contract=contract,
                                   form=request.form, today=date.today())

        old_weekly = float(contract.weekly_amount)
        _populate(contract, request.form)

        # Recalculate weeks_completed with new weekly amount if it changed
        if float(contract.weekly_amount) != old_weekly:
            contract.recalculate_weeks()

        _log("EDIT_CONTRACT", contract)
        db.session.commit()

        flash(f"Contract #{contract.id} updated successfully.", "success")
        return redirect(url_for("contracts.view", contract_id=contract_id))

    return render_template(
        "contracts/edit.html",
        contract=contract,
        form={},
        today=date.today(),
    )


@contracts_bp.route("/<int:contract_id>/complete", methods=["POST"])
@login_required
def complete(contract_id):
    """Mark a contract as fully paid and completed. Releases the vehicle."""
    contract = Contract.query.get_or_404(contract_id)

    if contract.status == "completed":
        flash("This contract is already marked completed.", "info")
        return redirect(url_for("contracts.view", contract_id=contract_id))

    contract.status         = "completed"
    contract.date_completed = datetime.utcnow()
    contract.weeks_completed = contract.total_weeks  # ensure 100%

    # Release vehicle back to available fleet
    vehicle = contract.vehicle
    vehicle.status = "available"
    _vehicle_event(
        vehicle, "contract_completed",
        f"Contract #{contract.id} completed — {contract.driver.full_name}",
        f"All {contract.total_weeks} weeks paid. Vehicle returned to fleet.",
    )
    _vehicle_event(vehicle, "returned",
                   f"Vehicle returned by {contract.driver.full_name}",
                   "Driver completed all hire-purchase payments.")

    _log("COMPLETE_CONTRACT", contract,
         f"Marked complete by {current_user.username}. "
         f"Total paid: ₦{contract.total_paid:,.0f}")
    db.session.commit()

    flash(
        f"Contract #{contract.id} marked as completed. "
        f"Vehicle {vehicle.vehicle_number} is now available.",
        "success",
    )
    return redirect(url_for("contracts.view", contract_id=contract_id))


@contracts_bp.route("/<int:contract_id>/suspend", methods=["POST"])
@login_required
def suspend(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    if contract.status != "active":
        flash("Only active contracts can be suspended.", "warning")
        return redirect(url_for("contracts.view", contract_id=contract_id))

    contract.status = "suspended"
    _log("SUSPEND_CONTRACT", contract)
    db.session.commit()

    flash(f"Contract #{contract.id} has been suspended.", "warning")
    return redirect(url_for("contracts.view", contract_id=contract_id))


@contracts_bp.route("/<int:contract_id>/reactivate", methods=["POST"])
@login_required
def reactivate(contract_id):
    contract = Contract.query.get_or_404(contract_id)

    if contract.status not in ("suspended", "inactive"):
        flash("Only suspended or inactive contracts can be reactivated.", "warning")
        return redirect(url_for("contracts.view", contract_id=contract_id))

    contract.status = "active"
    _log("REACTIVATE_CONTRACT", contract)
    db.session.commit()

    flash(f"Contract #{contract.id} has been reactivated.", "success")
    return redirect(url_for("contracts.view", contract_id=contract_id))


@contracts_bp.route("/<int:contract_id>/archive", methods=["POST"])
@login_required
def archive(contract_id):
    """Soft-archive an inactive or completed contract. Never deletes data."""
    contract = Contract.query.get_or_404(contract_id)

    if contract.status == "archived":
        flash("This contract is already archived.", "info")
        return redirect(url_for("contracts.view", contract_id=contract_id))

    if contract.status == "active":
        flash(
            "An active contract cannot be archived directly. "
            "Suspend or complete it first.",
            "danger",
        )
        return redirect(url_for("contracts.view", contract_id=contract_id))

    contract.status        = "archived"
    contract.date_archived = datetime.utcnow()

    _log("ARCHIVE_CONTRACT", contract)
    db.session.commit()

    flash(f"Contract #{contract.id} has been archived.", "warning")
    return redirect(url_for("contracts.index"))
