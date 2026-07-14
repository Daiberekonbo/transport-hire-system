from datetime import date, datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required
from backend.extensions import db
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.models.contract import Contract
from backend.models.payment import Payment
from backend.models.expense import Expense

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/")
@login_required
def index():
    today = date.today()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # Summary stats
    total_drivers = Driver.query.filter_by(status="active").count()
    total_vehicles = Vehicle.query.count()
    active_contracts = Contract.query.filter_by(status="active").count()

    # Revenue this week
    weekly_payments = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).filter(
        Payment.payment_date >= week_start,
        Payment.is_archived == False,
    ).scalar()

    # Revenue this month
    monthly_payments = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).filter(
        Payment.payment_date >= month_start,
        Payment.is_archived == False,
    ).scalar()

    # Total outstanding across all active contracts.
    # Computed in Python via Contract.outstanding_balance (same property used
    # on the Contract detail page and in Capital Management) so this figure
    # always matches what's shown elsewhere — it accounts for extra
    # expenditure, excludes archived/voided payments, and is clamped at 0
    # per contract instead of allowing negative contracts to offset others.
    total_outstanding = sum(
        c.outstanding_balance
        for c in Contract.query.filter_by(status="active").all()
    )

    # Outstanding loans
    outstanding_loans = db.session.query(
        db.func.coalesce(db.func.sum(Expense.amount - Expense.amount_repaid), 0)
    ).filter(
        Expense.status != "paid",
        Expense.is_archived == False,
    ).scalar()

    # Today's snapshot counts
    payments_today_count = Payment.query.filter(
        Payment.payment_date == today,
        Payment.is_archived == False,
    ).count()

    payments_today_amount = db.session.query(
        db.func.coalesce(db.func.sum(Payment.amount), 0)
    ).filter(
        Payment.payment_date == today,
        Payment.is_archived == False,
    ).scalar()

    expenses_today_count = Expense.query.filter(
        db.func.date(Expense.created_at) == today,
        Expense.is_archived == False,
    ).count()

    # Recent payments (last 10)
    recent_payments = (
        Payment.query
        .filter_by(is_archived=False)
        .order_by(Payment.created_at.desc())
        .limit(10)
        .all()
    )

    # Contracts expiring soon (within 4 weeks)
    expiring_contracts = (
        Contract.query
        .filter(
            Contract.status == "active",
            Contract.expected_end_date != None,
            Contract.expected_end_date <= today + timedelta(weeks=4),
        )
        .all()
    )

    # Vehicles by status
    vehicles_available = Vehicle.query.filter_by(status="available").count()
    vehicles_assigned = Vehicle.query.filter_by(status="assigned").count()

    return render_template(
        "dashboard/index.html",
        total_drivers=total_drivers,
        total_vehicles=total_vehicles,
        active_contracts=active_contracts,
        weekly_payments=weekly_payments,
        monthly_payments=monthly_payments,
        total_outstanding=total_outstanding or 0,
        outstanding_loans=outstanding_loans or 0,
        recent_payments=recent_payments,
        expiring_contracts=expiring_contracts,
        vehicles_available=vehicles_available,
        vehicles_assigned=vehicles_assigned,
        today=today,
        now=datetime.now(),
        payments_today_count=payments_today_count,
        payments_today_amount=payments_today_amount or 0,
        expenses_today_count=expenses_today_count,
    )
