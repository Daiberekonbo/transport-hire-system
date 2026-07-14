"""
Capital Management Routes
==========================

Everything on this page is computed live from existing data — Vehicle
purchase costs, Payments, Extra Expenditures — plus one new table,
CapitalAdjustment, for manual owner injections/withdrawals. Nothing here
duplicates or migrates existing data; it is a read-and-aggregate layer on
top of the current schema.

Routes
------
GET  /capital/                — dashboard summary + filterable transaction ledger
GET  /capital/adjust           — manual capital adjustment form (owner only)
POST /capital/adjust           — save adjustment (owner only)

Calculations
------------
Current Capital (Net Capital Position) =
    Vehicle Purchase Cost
  + Manual Capital Added
  - Extra Expenditure
  + Payments Received
  - Capital Withdrawals

Every figure is derived from live queries — nothing is hardcoded or cached.
"""

from functools import wraps
from datetime import datetime, date

from flask import Blueprint, render_template, redirect, url_for, flash, request, abort
from flask_login import login_required, current_user

from backend.extensions import db
from backend.models.vehicle import Vehicle
from backend.models.payment import Payment
from backend.models.expense import Expense
from backend.models.contract import Contract
from backend.models.driver import Driver
from backend.models.user import User
from backend.models.audit import AuditLog
from backend.models.capital import CapitalAdjustment
from backend.utils import parse_date as _parse_date, parse_amount as _parse_amount

capital_bp = Blueprint("capital", __name__)


# ─── Transaction-type display metadata ────────────────────────────────────────

CATEGORY_TO_TXN_TYPE = {
    "vehicle_repairs":  "Repair",
    "accident_repairs": "Repair",
    "servicing":        "Other Expense",
    "fuel_advance":     "Fuel",
    "driver_loan":      "Driver Loan",
    "spare_parts":      "Tyres",
    "insurance":        "Insurance",
    "fines":            "Other Expense",
    "other":            "Other Expense",
}

TXN_TYPES = [
    "Vehicle Purchase", "Extra Expenditure", "Driver Loan", "Fuel", "Repair",
    "Insurance", "Tyres", "Other Expense", "Payment Received",
    "Manual Capital Adjustment",
]

TXN_TYPE_META = {
    # type_label: (color, icon)
    "Vehicle Purchase":          ("primary",   "bi-truck-front-fill"),
    "Driver Loan":                ("purple",   "bi-cash-coin"),
    "Fuel":                       ("primary",  "bi-fuel-pump-fill"),
    "Repair":                     ("warning",  "bi-wrench-adjustable-circle"),
    "Insurance":                  ("success",  "bi-shield-check-fill"),
    "Tyres":                      ("secondary","bi-circle-fill"),
    "Other Expense":              ("secondary","bi-three-dots-vertical"),
    "Payment Received":           ("success",  "bi-cash-stack"),
    "Manual Capital Adjustment":  ("info",     "bi-bank2"),
}


def owner_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != "owner":
            abort(403)
        return f(*args, **kwargs)
    return decorated


def _as_date(value):
    """Coerce a date/datetime into a plain date for sorting/filtering."""
    if value is None:
        return date.min
    if isinstance(value, datetime):
        return value.date()
    return value


# ─── Summary calculations ──────────────────────────────────────────────────────

def _summary():
    vehicle_purchase_cost = float(
        db.session.query(db.func.coalesce(db.func.sum(Vehicle.purchase_price), 0)).scalar() or 0
    )
    extra_expenditure = float(
        db.session.query(db.func.coalesce(db.func.sum(Expense.amount), 0))
        .filter(Expense.is_archived == False).scalar() or 0
    )
    payments_received = float(
        db.session.query(db.func.coalesce(db.func.sum(Payment.amount), 0))
        .filter(Payment.is_archived == False).scalar() or 0
    )
    manual_added = float(
        db.session.query(db.func.coalesce(db.func.sum(CapitalAdjustment.amount), 0))
        .filter(CapitalAdjustment.type == "add").scalar() or 0
    )
    manual_withdrawn = float(
        db.session.query(db.func.coalesce(db.func.sum(CapitalAdjustment.amount), 0))
        .filter(CapitalAdjustment.type == "withdraw").scalar() or 0
    )
    outstanding_balance = sum(
        c.outstanding_balance
        for c in Contract.query.filter(Contract.status != "archived").all()
    )

    total_capital_invested = vehicle_purchase_cost + manual_added
    net_capital_position = (
        vehicle_purchase_cost + manual_added - extra_expenditure
        + payments_received - manual_withdrawn
    )

    return {
        "total_capital_invested": total_capital_invested,
        "vehicle_purchase_cost":  vehicle_purchase_cost,
        "extra_expenditure":      extra_expenditure,
        "payments_received":      payments_received,
        "outstanding_balance":    outstanding_balance,
        "net_capital_position":   net_capital_position,
        "manual_added":           manual_added,
        "manual_withdrawn":       manual_withdrawn,
    }


# ─── Unified transaction ledger ────────────────────────────────────────────────

def _build_ledger():
    """
    Merge Vehicle purchases, Expenses, Payments and CapitalAdjustments into a
    single chronological ledger with a running balance, matching the formula:

        Current Capital = Vehicle Purchase Cost + Manual Capital Added
                           - Extra Expenditure + Payments Received
                           - Capital Withdrawals
    """
    # Pre-fetch "performed by" for vehicle purchases from the audit trail
    # (ADD_VEHICLE entries) so we don't need a new column on Vehicle.
    add_vehicle_logs = {
        log.entity_id: log.user_id
        for log in AuditLog.query.filter_by(entity_type="Vehicle", action="ADD_VEHICLE").all()
    }
    users_by_id = {u.id: u for u in User.query.all()}

    txns = []

    for v in Vehicle.query.all():
        cost = float(v.purchase_price or 0)
        if cost <= 0:
            continue
        performer = users_by_id.get(add_vehicle_logs.get(v.id))
        txns.append({
            "date": _as_date(v.purchase_date or v.date_registered),
            "sort_key": (_as_date(v.purchase_date or v.date_registered), v.id, 0),
            "type": "Vehicle Purchase",
            "description": f"Purchase of vehicle {v.vehicle_number}"
                            + (f" ({v.manufacturer} {v.model})".strip() if v.manufacturer or v.model else ""),
            "amount": cost,
            "driver": v.current_driver,
            "vehicle": v,
            "performed_by": performer.username if performer else "—",
        })

    for e in Expense.query.filter_by(is_archived=False).all():
        txn_type = CATEGORY_TO_TXN_TYPE.get(e.category, "Other Expense")
        txns.append({
            "date": _as_date(e.expense_date),
            "sort_key": (_as_date(e.expense_date), e.id, 1),
            "type": txn_type,
            "description": f"{e.display_title} — {e.expense_number or ('#' + str(e.id))}",
            "amount": -float(e.amount or 0),
            "driver": e.driver,
            "vehicle": e.vehicle,
            "performed_by": e.recorder.username if e.recorder else "—",
        })

    for p in Payment.query.filter_by(is_archived=False).all():
        txns.append({
            "date": _as_date(p.payment_date),
            "sort_key": (_as_date(p.payment_date), p.id, 2),
            "type": "Payment Received",
            "description": f"Payment received — {p.receipt_number or ('#' + str(p.id))}",
            "amount": float(p.amount or 0),
            "driver": p.driver,
            "vehicle": p.contract.vehicle if p.contract else None,
            "performed_by": p.recorder.username if getattr(p, "recorder", None) else (
                users_by_id.get(p.recorded_by).username if users_by_id.get(p.recorded_by) else "—"
            ),
        })

    for a in CapitalAdjustment.query.all():
        txns.append({
            "date": _as_date(a.adjustment_date),
            "sort_key": (_as_date(a.adjustment_date), a.id, 3),
            "type": "Manual Capital Adjustment",
            "description": f"{a.type_label}: {a.reason}",
            "amount": a.signed_amount,
            "driver": None,
            "vehicle": None,
            "performed_by": a.recorder.username if a.recorder else "—",
        })

    # Chronological (oldest first) to compute a true running balance.
    txns.sort(key=lambda t: t["sort_key"])
    balance = 0.0
    for t in txns:
        balance += t["amount"]
        t["running_balance"] = balance

    return txns


class _SimplePagination:
    """Minimal Flask-SQLAlchemy-Pagination-compatible wrapper for an in-memory list,
    so we can reuse the exact same pagination template pattern used elsewhere."""

    def __init__(self, items_all, page, per_page):
        self.page = page
        self.per_page = per_page
        self.total = len(items_all)
        self.pages = max(1, (self.total + per_page - 1) // per_page)
        self.page = min(max(1, page), self.pages)
        start = (self.page - 1) * per_page
        self.items = items_all[start:start + per_page]
        self.has_prev = self.page > 1
        self.has_next = self.page < self.pages
        self.prev_num = self.page - 1
        self.next_num = self.page + 1

    def iter_pages(self, left_edge=1, right_edge=1, left_current=2, right_current=2):
        last = 0
        for num in range(1, self.pages + 1):
            if (num <= left_edge or
                    (self.page - left_current - 1 < num < self.page + right_current + 1) or
                    num > self.pages - right_edge):
                if last + 1 != num:
                    yield None
                yield num
                last = num


# ─── routes ───────────────────────────────────────────────────────────────────

@capital_bp.route("/")
@login_required
def index():
    summary = _summary()
    ledger = _build_ledger()

    search      = request.args.get("q", "").strip()
    type_filter = request.args.get("type", "")
    driver_f    = request.args.get("driver_id", "")
    vehicle_f   = request.args.get("vehicle_id", "")
    date_from_s = request.args.get("date_from", "")
    date_to_s   = request.args.get("date_to", "")
    amt_min_s   = request.args.get("amt_min", "")
    amt_max_s   = request.args.get("amt_max", "")
    page        = request.args.get("page", 1, type=int)

    filtered = ledger

    if search:
        like = search.lower()
        filtered = [
            t for t in filtered
            if like in (t["description"] or "").lower()
            or (t["driver"] and like in t["driver"].full_name.lower())
            or (t["vehicle"] and like in t["vehicle"].vehicle_number.lower())
            or like in (t["performed_by"] or "").lower()
        ]
    if type_filter:
        filtered = [t for t in filtered if t["type"] == type_filter]
    if driver_f:
        filtered = [t for t in filtered if t["driver"] and str(t["driver"].id) == driver_f]
    if vehicle_f:
        filtered = [t for t in filtered if t["vehicle"] and str(t["vehicle"].id) == vehicle_f]

    df = _parse_date(date_from_s)
    dt = _parse_date(date_to_s)
    if df:
        filtered = [t for t in filtered if t["date"] >= df]
    if dt:
        filtered = [t for t in filtered if t["date"] <= dt]

    amt_min = _parse_amount(amt_min_s)
    amt_max = _parse_amount(amt_max_s)
    if amt_min > 0:
        filtered = [t for t in filtered if abs(t["amount"]) >= amt_min]
    if amt_max > 0:
        filtered = [t for t in filtered if abs(t["amount"]) <= amt_max]

    # Newest first for display.
    filtered = list(reversed(filtered))

    txns_page = _SimplePagination(filtered, page, 25)

    drivers  = Driver.query.order_by(Driver.full_name).all()
    vehicles = Vehicle.query.order_by(Vehicle.vehicle_number).all()

    return render_template(
        "capital/index.html",
        summary=summary,
        txns=txns_page,
        txn_types=TXN_TYPES,
        txn_meta=TXN_TYPE_META,
        drivers=drivers,
        vehicles=vehicles,
        search=search,
        type_filter=type_filter,
        driver_f=driver_f,
        vehicle_f=vehicle_f,
        date_from_s=date_from_s,
        date_to_s=date_to_s,
        amt_min_s=amt_min_s,
        amt_max_s=amt_max_s,
    )


@capital_bp.route("/adjust", methods=["GET", "POST"])
@login_required
@owner_required
def adjust():
    if request.method == "POST":
        adj_type = request.form.get("type", "")
        if adj_type not in ("add", "withdraw"):
            flash("Please choose whether you are adding or withdrawing capital.", "danger")
            return render_template("capital/adjust.html", form=request.form, today=date.today())

        amount = _parse_amount(request.form.get("amount", "0"))
        if amount <= 0:
            flash("Amount must be greater than zero.", "danger")
            return render_template("capital/adjust.html", form=request.form, today=date.today())

        reason = request.form.get("reason", "").strip()
        if not reason:
            flash("A reason is required for every capital adjustment.", "danger")
            return render_template("capital/adjust.html", form=request.form, today=date.today())

        adj_date = _parse_date(request.form.get("adjustment_date", "")) or date.today()

        if adj_type == "withdraw":
            summary = _summary()
            if amount > summary["net_capital_position"]:
                flash(
                    f"Cannot withdraw ₦{amount:,.0f} — current capital position is only "
                    f"₦{summary['net_capital_position']:,.0f}.",
                    "danger",
                )
                return render_template("capital/adjust.html", form=request.form, today=date.today())

        adjustment = CapitalAdjustment(
            type=adj_type,
            amount=amount,
            reason=reason,
            adjustment_date=adj_date,
            recorded_by=current_user.id,
        )
        db.session.add(adjustment)
        db.session.flush()

        action = "ADD_CAPITAL" if adj_type == "add" else "WITHDRAW_CAPITAL"
        db.session.add(AuditLog(
            user_id=current_user.id,
            action=action,
            entity_type="Capital",
            entity_id=adjustment.id,
            description=f"{adjustment.type_label}: ₦{amount:,.0f} — {reason}",
            ip_address=request.remote_addr,
            user_agent=(request.headers.get("User-Agent") or "")[:255],
        ))
        db.session.commit()

        verb = "added to" if adj_type == "add" else "withdrawn from"
        flash(f"₦{amount:,.0f} {verb} capital successfully.", "success")
        return redirect(url_for("capital.index"))

    return render_template("capital/adjust.html", form={}, today=date.today())
