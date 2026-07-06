"""
Extra Expenditure Management Routes
=====================================

Routes
------
GET  /expenses/                           — list with filters (driver/vehicle/category/date/amount)
GET  /expenses/add                        — add form (select contract)
GET  /expenses/add?contract_id=X          — add form pre-loaded for contract X
POST /expenses/add                        — save new expenditure
GET  /expenses/<id>                       — expenditure detail
GET  /expenses/<id>/edit                  — edit form (developer/owner only)
POST /expenses/<id>/edit                  — save edit
POST /expenses/<id>/void                  — void/archive (developer only)
GET  /expenses/history/<contract_id>      — all expenditures for one contract (printable)
GET  /expenses/report                     — aggregate printable report
GET  /expenses/by-driver/<driver_id>      — expenditures for one driver
GET  /expenses/by-vehicle/<vehicle_id>    — expenditures for one vehicle

Business rules
--------------
• Every expenditure is permanently linked to an active contract.
• Adding an expense automatically increases that contract's outstanding_balance
  (Contract.total_extra_expenditure sums all non-archived expenses).
• contract.recalculate_weeks() is NOT called here — week progress is based only
  on payments, not expenses. Outstanding balance rises instead.
• Editing and voiding require developer or owner role.
• Every creation, edit and void attempt is recorded in AuditLog.
• Receipt/document uploads are stored in static/uploads/expenses/.
"""

import os
from datetime import datetime, date, time as dtime
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, abort, current_app)
from flask_login import login_required, current_user
from sqlalchemy import or_
from werkzeug.utils import secure_filename

from backend.extensions import db
from backend.models.expense import Expense, CATEGORIES
from backend.models.contract import Contract
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.models.audit import AuditLog

expenses_bp = Blueprint("expenses", __name__)

ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg", "gif", "webp"}


# ─── helpers ──────────────────────────────────────────────────────────────────

def _can_edit():
    return current_user.role in ("developer", "owner")


def _log(action: str, expense: Expense, extra: str = ""):
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Expense",
        entity_id=expense.id,
        description=(
            f"{action}: {expense.expense_number or ('#' + str(expense.id))} "
            f"— {expense.display_title} "
            f"₦{float(expense.amount):,.0f} "
            f"driver={expense.driver.full_name} contract=#{expense.contract_id}"
            + (f". {extra}" if extra else "")
        ),
    ))


def _generate_expense_number(expense: Expense) -> str:
    now = datetime.utcnow()
    return f"EXP-{now.year}{now.month:02d}-{expense.id:05d}"


def _allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def _save_upload(file_obj) -> str | None:
    """Save uploaded file to static/uploads/expenses/; return stored filename or None."""
    if not file_obj or file_obj.filename == "":
        return None
    if not _allowed_file(file_obj.filename):
        return None
    upload_dir = os.path.join(current_app.config["UPLOAD_FOLDER"], "expenses")
    os.makedirs(upload_dir, exist_ok=True)
    filename = secure_filename(file_obj.filename)
    # prepend timestamp to avoid collisions
    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    stored_name = f"{ts}_{filename}"
    file_obj.save(os.path.join(upload_dir, stored_name))
    return stored_name


def _active_contracts_for_select():
    """Return active contracts ordered by driver name, for dropdowns."""
    return (Contract.query
            .filter_by(status="active")
            .join(Driver, Contract.driver_id == Driver.id)
            .order_by(Driver.full_name)
            .all())


def _parse_date(s: str):
    try:
        return datetime.strptime(s.strip(), "%Y-%m-%d").date()
    except (ValueError, AttributeError):
        return None


def _parse_time(s: str):
    try:
        parts = s.strip().split(":")
        return dtime(int(parts[0]), int(parts[1]))
    except Exception:
        return None


def _parse_amount(s: str) -> float:
    try:
        return float(str(s).replace(",", "").strip())
    except (ValueError, TypeError):
        return 0.0


# ─── list ─────────────────────────────────────────────────────────────────────

@expenses_bp.route("/")
@login_required
def index():
    search       = request.args.get("q",         "").strip()
    cat_filter   = request.args.get("category",  "")
    driver_f     = request.args.get("driver_id", "", type=str)
    vehicle_f    = request.args.get("vehicle_id","", type=str)
    date_from_s  = request.args.get("date_from", "")
    date_to_s    = request.args.get("date_to",   "")
    amt_min_s    = request.args.get("amt_min",   "")
    amt_max_s    = request.args.get("amt_max",   "")
    page         = request.args.get("page", 1, type=int)

    query = (
        Expense.query
        .join(Driver,   Expense.driver_id   == Driver.id)
        .join(Contract, Expense.contract_id == Contract.id)
        .join(Vehicle,  Contract.vehicle_id == Vehicle.id)
        .filter(Expense.is_archived == False)
        .order_by(Expense.expense_date.desc(), Expense.created_at.desc())
    )

    if search:
        like = f"%{search}%"
        query = query.filter(or_(
            Driver.full_name.ilike(like),
            Expense.title.ilike(like),
            Expense.description.ilike(like),
            Expense.reason.ilike(like),
            Expense.expense_number.ilike(like),
            Vehicle.vehicle_number.ilike(like),
        ))
    if cat_filter:
        query = query.filter(Expense.category == cat_filter)
    if driver_f:
        query = query.filter(Expense.driver_id == int(driver_f))
    if vehicle_f:
        query = query.filter(Contract.vehicle_id == int(vehicle_f))

    df = _parse_date(date_from_s)
    dt = _parse_date(date_to_s)
    if df:
        query = query.filter(Expense.expense_date >= df)
    if dt:
        query = query.filter(Expense.expense_date <= dt)

    amt_min = _parse_amount(amt_min_s)
    amt_max = _parse_amount(amt_max_s)
    if amt_min > 0:
        query = query.filter(Expense.amount >= amt_min)
    if amt_max > 0:
        query = query.filter(Expense.amount <= amt_max)

    expenses = query.paginate(page=page, per_page=25, error_out=False)
    total_amount = sum(float(e.amount) for e in expenses.items)

    # Totals by category (for current filtered page, full query totals)
    all_filtered = query.all()
    cat_totals = {}
    for e in all_filtered:
        cat_totals[e.category] = cat_totals.get(e.category, 0) + float(e.amount)

    grand_total = sum(cat_totals.values())

    drivers  = Driver.query.filter_by(status="active").order_by(Driver.full_name).all()
    vehicles = Vehicle.query.order_by(Vehicle.vehicle_number).all()

    return render_template(
        "expenses/index.html",
        expenses=expenses,
        total_amount=total_amount,
        grand_total=grand_total,
        cat_totals=cat_totals,
        categories=CATEGORIES,
        drivers=drivers,
        vehicles=vehicles,
        search=search,
        cat_filter=cat_filter,
        driver_f=driver_f,
        vehicle_f=vehicle_f,
        date_from_s=date_from_s,
        date_to_s=date_to_s,
        amt_min_s=amt_min_s,
        amt_max_s=amt_max_s,
    )


# ─── add ──────────────────────────────────────────────────────────────────────

@expenses_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    preselect_contract_id = request.args.get("contract_id", type=int)
    active_contracts = _active_contracts_for_select()

    if request.method == "POST":
        contract_id = request.form.get("contract_id", type=int)
        if not contract_id:
            flash("Please select a contract.", "danger")
            return render_template("expenses/add.html",
                                   active_contracts=active_contracts,
                                   categories=CATEGORIES,
                                   preselect_contract_id=preselect_contract_id,
                                   today=date.today(), form=request.form)

        contract = Contract.query.get_or_404(contract_id)
        if contract.status not in ("active", "suspended"):
            flash("Expenditures can only be added against active or suspended contracts.", "danger")
            return redirect(url_for("expenses.add"))

        title = request.form.get("title", "").strip()
        if not title:
            flash("Please enter an expenditure title.", "danger")
            return render_template("expenses/add.html",
                                   active_contracts=active_contracts,
                                   categories=CATEGORIES,
                                   preselect_contract_id=contract_id,
                                   today=date.today(), form=request.form)

        amount = _parse_amount(request.form.get("amount", "0"))
        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template("expenses/add.html",
                                   active_contracts=active_contracts,
                                   categories=CATEGORIES,
                                   preselect_contract_id=contract_id,
                                   today=date.today(), form=request.form)

        exp_date = _parse_date(request.form.get("expense_date", "")) or date.today()
        exp_time = _parse_time(request.form.get("expense_time", ""))

        # Handle file upload
        receipt_stored = None
        if "receipt_file" in request.files:
            receipt_stored = _save_upload(request.files["receipt_file"])

        expense = Expense(
            driver_id    = contract.driver_id,
            vehicle_id   = contract.vehicle_id,
            contract_id  = contract.id,
            title        = title,
            category     = request.form.get("category", "other"),
            description  = request.form.get("description", "").strip() or None,
            reason       = request.form.get("description", "").strip() or None,  # keep legacy in sync
            amount       = amount,
            expense_date = exp_date,
            expense_time = exp_time,
            approved_by  = request.form.get("approved_by", "").strip() or None,
            notes        = request.form.get("notes", "").strip() or None,
            receipt_file = receipt_stored,
            recorded_by  = current_user.id,
            status       = "outstanding",
        )

        db.session.add(expense)
        db.session.flush()  # get expense.id

        expense.expense_number = _generate_expense_number(expense)
        db.session.flush()

        _log("ADD_EXPENSE", expense,
             f"Category: {expense.category_label}. Contract #{contract.id} outstanding balance updated.")
        db.session.commit()

        flash(
            f"Expenditure of ₦{amount:,.0f} recorded as {expense.expense_number}. "
            f"Contract #{contract.id} outstanding balance has been updated.",
            "success",
        )
        return redirect(url_for("expenses.view", expense_id=expense.id))

    return render_template(
        "expenses/add.html",
        active_contracts=active_contracts,
        categories=CATEGORIES,
        preselect_contract_id=preselect_contract_id,
        today=date.today(),
        form={},
    )


# ─── view ─────────────────────────────────────────────────────────────────────

@expenses_bp.route("/<int:expense_id>")
@login_required
def view(expense_id):
    expense  = Expense.query.get_or_404(expense_id)
    contract = Contract.query.get(expense.contract_id) if expense.contract_id else None
    can_edit = _can_edit()
    return render_template(
        "expenses/view.html",
        expense=expense,
        contract=contract,
        can_edit=can_edit,
        categories=CATEGORIES,
    )


# ─── edit ─────────────────────────────────────────────────────────────────────

@expenses_bp.route("/<int:expense_id>/edit", methods=["GET", "POST"])
@login_required
def edit(expense_id):
    if not _can_edit():
        flash("Only developers and owners can edit expenditure records.", "danger")
        return redirect(url_for("expenses.view", expense_id=expense_id))

    expense  = Expense.query.get_or_404(expense_id)
    if expense.is_archived:
        flash("This expenditure has been voided and cannot be edited.", "warning")
        return redirect(url_for("expenses.view", expense_id=expense_id))

    active_contracts = _active_contracts_for_select()

    if request.method == "POST":
        old_amount = float(expense.amount)

        expense.title       = request.form.get("title", expense.title).strip()
        expense.category    = request.form.get("category", expense.category)
        expense.description = request.form.get("description", "").strip() or None
        expense.reason      = expense.description  # keep legacy in sync
        expense.approved_by = request.form.get("approved_by", "").strip() or None
        expense.notes       = request.form.get("notes", "").strip() or None

        new_amount = _parse_amount(request.form.get("amount", str(old_amount)))
        if new_amount > 0:
            expense.amount = new_amount

        new_date = _parse_date(request.form.get("expense_date", ""))
        if new_date:
            expense.expense_date = new_date
        new_time = _parse_time(request.form.get("expense_time", ""))
        if new_time:
            expense.expense_time = new_time

        # Handle new receipt upload
        if "receipt_file" in request.files:
            stored = _save_upload(request.files["receipt_file"])
            if stored:
                expense.receipt_file = stored

        _log("EDIT_EXPENSE", expense,
             f"Amount changed: ₦{old_amount:,.0f} → ₦{float(expense.amount):,.0f}")
        db.session.commit()

        flash(f"Expenditure {expense.expense_number} updated successfully.", "success")
        return redirect(url_for("expenses.view", expense_id=expense_id))

    return render_template(
        "expenses/edit.html",
        expense=expense,
        active_contracts=active_contracts,
        categories=CATEGORIES,
        today=date.today(),
    )


# ─── void ─────────────────────────────────────────────────────────────────────

@expenses_bp.route("/<int:expense_id>/void", methods=["POST"])
@login_required
def void(expense_id):
    if not _can_edit():
        flash("Only developers and owners can void expenditure records.", "danger")
        return redirect(url_for("expenses.view", expense_id=expense_id))

    expense = Expense.query.get_or_404(expense_id)
    if expense.is_archived:
        flash("This expenditure has already been voided.", "info")
        return redirect(url_for("expenses.view", expense_id=expense_id))

    expense.is_archived = True
    contract_id = expense.contract_id

    _log("VOID_EXPENSE", expense, "Voided — removed from contract outstanding balance.")
    db.session.commit()

    flash(
        f"Expenditure {expense.expense_number} has been voided. "
        f"Contract outstanding balance has been updated.",
        "warning",
    )
    if contract_id:
        return redirect(url_for("expenses.history", contract_id=contract_id))
    return redirect(url_for("expenses.index"))


# ─── history (per contract) ───────────────────────────────────────────────────

@expenses_bp.route("/history/<int:contract_id>")
@login_required
def history(contract_id):
    contract  = Contract.query.get_or_404(contract_id)
    printable = request.args.get("print", "") == "1"

    expenses_q = (
        Expense.query
        .filter_by(contract_id=contract_id, is_archived=False)
        .order_by(Expense.expense_date.asc(), Expense.created_at.asc())
    )

    if printable:
        all_expenses = expenses_q.all()
        total = sum(float(e.amount) for e in all_expenses)
        return render_template(
            "expenses/history.html",
            contract=contract,
            expenses=all_expenses,
            total=total,
            printable=True,
            printed_at=datetime.utcnow(),
            categories=CATEGORIES,
            can_edit=_can_edit(),
        )

    page     = request.args.get("page", 1, type=int)
    exp_pg   = expenses_q.paginate(page=page, per_page=30, error_out=False)
    total    = sum(float(e.amount) for e in expenses_q.all())

    return render_template(
        "expenses/history.html",
        contract=contract,
        expenses=exp_pg,
        total=total,
        printable=False,
        printed_at=None,
        categories=CATEGORIES,
        can_edit=_can_edit(),
    )


# ─── report (aggregate / printable) ──────────────────────────────────────────

@expenses_bp.route("/report")
@login_required
def report():
    cat_filter  = request.args.get("category", "")
    date_from_s = request.args.get("date_from", "")
    date_to_s   = request.args.get("date_to",   "")
    driver_f    = request.args.get("driver_id", "")
    vehicle_f   = request.args.get("vehicle_id","")
    printable   = request.args.get("print", "") == "1"

    query = (
        Expense.query
        .join(Driver,   Expense.driver_id   == Driver.id)
        .join(Contract, Expense.contract_id == Contract.id)
        .join(Vehicle,  Contract.vehicle_id == Vehicle.id)
        .filter(Expense.is_archived == False)
        .order_by(Expense.expense_date.desc())
    )

    if cat_filter:
        query = query.filter(Expense.category == cat_filter)
    if driver_f:
        query = query.filter(Expense.driver_id == int(driver_f))
    if vehicle_f:
        query = query.filter(Contract.vehicle_id == int(vehicle_f))

    df = _parse_date(date_from_s)
    dt = _parse_date(date_to_s)
    if df:
        query = query.filter(Expense.expense_date >= df)
    if dt:
        query = query.filter(Expense.expense_date <= dt)

    all_expenses = query.all()

    # Aggregate by category
    by_category = {}
    for e in all_expenses:
        if e.category not in by_category:
            by_category[e.category] = {"label": e.category_label, "count": 0, "total": 0.0}
        by_category[e.category]["count"] += 1
        by_category[e.category]["total"] += float(e.amount)

    # Aggregate by driver
    by_driver = {}
    for e in all_expenses:
        key = e.driver_id
        if key not in by_driver:
            by_driver[key] = {"name": e.driver.full_name, "count": 0, "total": 0.0}
        by_driver[key]["count"] += 1
        by_driver[key]["total"] += float(e.amount)

    # Aggregate by vehicle
    by_vehicle = {}
    for e in all_expenses:
        if e.vehicle_id:
            key = e.vehicle_id
            if key not in by_vehicle:
                by_vehicle[key] = {
                    "number": e.vehicle.vehicle_number if e.vehicle else "—",
                    "count": 0, "total": 0.0
                }
            by_vehicle[key]["count"] += 1
            by_vehicle[key]["total"] += float(e.amount)

    grand_total = sum(float(e.amount) for e in all_expenses)

    drivers  = Driver.query.order_by(Driver.full_name).all()
    vehicles = Vehicle.query.order_by(Vehicle.vehicle_number).all()

    return render_template(
        "expenses/report.html",
        expenses=all_expenses,
        by_category=by_category,
        by_driver=dict(sorted(by_driver.items(), key=lambda x: x[1]["total"], reverse=True)),
        by_vehicle=dict(sorted(by_vehicle.items(), key=lambda x: x[1]["total"], reverse=True)),
        grand_total=grand_total,
        categories=CATEGORIES,
        drivers=drivers,
        vehicles=vehicles,
        cat_filter=cat_filter,
        date_from_s=date_from_s,
        date_to_s=date_to_s,
        driver_f=driver_f,
        vehicle_f=vehicle_f,
        printable=printable,
        printed_at=datetime.utcnow() if printable else None,
    )


# ─── by-driver ────────────────────────────────────────────────────────────────

@expenses_bp.route("/by-driver/<int:driver_id>")
@login_required
def by_driver(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    expenses = (
        Expense.query
        .filter_by(driver_id=driver_id, is_archived=False)
        .order_by(Expense.expense_date.desc())
        .all()
    )
    total = sum(float(e.amount) for e in expenses)
    return render_template(
        "expenses/by_driver.html",
        driver=driver,
        expenses=expenses,
        total=total,
        categories=CATEGORIES,
        can_edit=_can_edit(),
    )


# ─── by-vehicle ───────────────────────────────────────────────────────────────

@expenses_bp.route("/by-vehicle/<int:vehicle_id>")
@login_required
def by_vehicle(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    expenses = (
        Expense.query
        .filter_by(vehicle_id=vehicle_id, is_archived=False)
        .order_by(Expense.expense_date.desc())
        .all()
    )
    total = sum(float(e.amount) for e in expenses)
    return render_template(
        "expenses/by_vehicle.html",
        vehicle=vehicle,
        expenses=expenses,
        total=total,
        categories=CATEGORIES,
        can_edit=_can_edit(),
    )
