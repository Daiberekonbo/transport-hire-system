"""
Archives — read-only browser for every soft-archived / voided record.

Nothing in THMS is ever hard-deleted. This page is the single place to see
everything that has been archived or voided across every module:

  - Drivers    (status == 'archived')            — restorable
  - Vehicles   (status == 'archived')             — restorable
  - Contracts  (status == 'archived')             — final; no restore route
  - Payments   (is_archived == True, i.e. voided) — final; no restore route
  - Expenses   (is_archived == True, i.e. voided) — final; no restore route

Tabs let the user switch between entity types; search applies to whichever
tab is currently active.
"""

from flask import Blueprint, render_template, request
from flask_login import login_required
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.models.contract import Contract
from backend.models.payment import Payment
from backend.models.expense import Expense

archives_bp = Blueprint("archives", __name__)

TABS = ("drivers", "vehicles", "contracts", "payments", "expenses")


@archives_bp.route("/")
@login_required
def index():
    tab = request.args.get("tab", "drivers")
    if tab not in TABS:
        tab = "drivers"
    search = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)

    counts = {
        "drivers":   Driver.query.filter(Driver.status == "archived").count(),
        "vehicles":  Vehicle.query.filter(Vehicle.status == "archived").count(),
        "contracts": Contract.query.filter(Contract.status == "archived").count(),
        "payments":  Payment.query.filter(Payment.is_archived == True).count(),
        "expenses":  Expense.query.filter(Expense.is_archived == True).count(),
    }

    records = None

    if tab == "drivers":
        query = Driver.query.filter(Driver.status == "archived")
        if search:
            query = query.filter(Driver.full_name.ilike(f"%{search}%"))
        records = query.order_by(Driver.date_archived.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

    elif tab == "vehicles":
        query = Vehicle.query.filter(Vehicle.status == "archived")
        if search:
            query = query.filter(Vehicle.vehicle_number.ilike(f"%{search}%"))
        records = query.order_by(Vehicle.date_archived.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

    elif tab == "contracts":
        query = (
            Contract.query
            .join(Driver, Contract.driver_id == Driver.id)
            .filter(Contract.status == "archived")
        )
        if search:
            query = query.filter(Driver.full_name.ilike(f"%{search}%"))
        records = query.order_by(Contract.date_archived.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

    elif tab == "payments":
        query = (
            Payment.query
            .join(Driver, Payment.driver_id == Driver.id)
            .filter(Payment.is_archived == True)
        )
        if search:
            query = query.filter(Driver.full_name.ilike(f"%{search}%"))
        records = query.order_by(Payment.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

    elif tab == "expenses":
        query = (
            Expense.query
            .join(Driver, Expense.driver_id == Driver.id)
            .filter(Expense.is_archived == True)
        )
        if search:
            query = query.filter(Driver.full_name.ilike(f"%{search}%"))
        records = query.order_by(Expense.created_at.desc()).paginate(
            page=page, per_page=20, error_out=False
        )

    return render_template(
        "archives/index.html",
        tab=tab,
        records=records,
        counts=counts,
        search=search,
    )
