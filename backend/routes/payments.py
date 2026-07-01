from datetime import datetime, date
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from backend.extensions import db
from backend.models.payment import Payment
from backend.models.driver import Driver
from backend.models.contract import Contract

payments_bp = Blueprint("payments", __name__)


@payments_bp.route("/")
@login_required
def index():
    page = request.args.get("page", 1, type=int)
    search = request.args.get("q", "")

    query = (
        Payment.query
        .join(Driver, Payment.driver_id == Driver.id)
        .filter(Payment.is_archived == False)
        .order_by(Payment.created_at.desc())
    )
    if search:
        query = query.filter(Driver.full_name.ilike(f"%{search}%"))

    payments = query.paginate(page=page, per_page=25, error_out=False)
    return render_template("payments/index.html", payments=payments, search=search)


@payments_bp.route("/record", methods=["GET", "POST"])
@login_required
def record():
    drivers = Driver.query.filter_by(status="active").order_by(Driver.full_name).all()

    if request.method == "POST":
        driver_id = request.form.get("driver_id", type=int)
        driver = Driver.query.get_or_404(driver_id)
        contract = driver.active_contract
        if not contract:
            flash("This driver has no active contract.", "danger")
            return redirect(url_for("payments.record"))

        amount = float(request.form.get("amount", 0))
        payment = Payment(
            contract_id=contract.id,
            driver_id=driver_id,
            amount=amount,
            payment_date=date.fromisoformat(request.form.get("payment_date", str(date.today()))),
            sender=request.form.get("sender"),
            receiver=request.form.get("receiver"),
            payment_method=request.form.get("payment_method", "cash"),
            bank_name=request.form.get("bank_name"),
            reference=request.form.get("reference"),
            notes=request.form.get("notes"),
            recorded_by=current_user.id,
        )
        db.session.add(payment)

        # Recalculate weeks completed
        total_paid = float(contract.total_paid) + amount
        if float(contract.weekly_amount) > 0:
            contract.weeks_completed = int(total_paid // float(contract.weekly_amount))

        db.session.commit()
        flash(f"Payment of ₦{amount:,.0f} recorded for {driver.full_name}.", "success")
        return redirect(url_for("payments.index"))

    return render_template("payments/record.html", drivers=drivers, today=date.today())
