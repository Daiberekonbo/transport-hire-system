"""
Payments Management Routes
===========================

Routes
------
GET  /payments/                         — full payment list with filters
GET  /payments/receipts                 — receipt search (by number, driver, vehicle, date)
GET  /payments/record                   — record form (driver/contract selection)
GET  /payments/record?contract_id=X     — record form pre-loaded for contract
POST /payments/record                   — save payment → redirect to view with receipt buttons
GET  /payments/overdue                  — overdue summary across all contracts
GET  /payments/<id>                     — payment detail (with View Receipt / Download PDF)
GET  /payments/<id>/receipt             — printable receipt (browser)
GET  /payments/<id>/receipt/pdf         — download PDF receipt
POST /payments/<id>/void                — void (soft-delete) a payment
GET  /payments/history/<contract_id>    — full payment history for one contract
GET  /payments/api/contract-info        — JSON: contract data for JS widget

Business logic
--------------
• week_from / week_to are computed from the contract's total paid BEFORE this
  payment, divided by weekly_amount. This is deterministic and self-correcting.
• Receipt numbers use a global monotonic counter — THMS-{YYYYMMDD}-{seq:06d}.
  The sequence never resets, never reuses a number, even after voids.
• Overdue = weeks elapsed since start_date − weeks_completed. Elapsed weeks
  are floor((today − start_date).days / 7).
• Voiding a payment recalculates contract.weeks_completed from remaining payments.
• Every mutation is recorded in AuditLog. Viewing / printing a receipt also logs.
"""

import json
from datetime import datetime, date, time as dtime
from io import BytesIO
from math import floor

from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, make_response)
from flask_login import login_required, current_user
from sqlalchemy import or_, func

from backend.extensions import db
from backend.models.payment import Payment
from backend.models.contract import Contract
from backend.models.driver import Driver
from backend.models.vehicle import Vehicle
from backend.models.audit import AuditLog

payments_bp = Blueprint("payments", __name__)


# ─── helpers ──────────────────────────────────────────────────────────────────

def _log(action: str, payment: Payment, extra: str = ""):
    db.session.add(AuditLog(
        user_id=current_user.id,
        action=action,
        entity_type="Payment",
        entity_id=payment.id,
        description=(
            f"{action}: receipt {payment.receipt_number or f'#{payment.id}'} "
            f"₦{float(payment.amount):,.0f} "
            f"for {payment.driver.full_name} — contract #{payment.contract_id}"
            + (f". {extra}" if extra else "")
        ),
        ip_address=request.remote_addr,
        user_agent=(request.headers.get("User-Agent") or "")[:255],
    ))


def _generate_receipt(payment: Payment) -> str:
    """
    Assign the next globally-unique, never-reused receipt number.
    Format: THMS-{YYYYMMDD}-{seq:06d}   e.g. THMS-20260714-000001
    Must be called inside an open session; caller commits.
    """
    from backend.models.receipt_seq import ReceiptSequence
    date_str = datetime.utcnow().strftime("%Y%m%d")
    return ReceiptSequence.next_number(date_str)


def _compute_week_coverage(contract: Contract, payment_amount: float):
    """
    Return (week_from, week_to) based on the contract's current total_paid
    BEFORE this payment.

    week_to < week_from signals a partial payment (doesn't complete week_from).
    """
    weekly = float(contract.weekly_amount or 0)
    if weekly <= 0:
        return 1, 0  # partial, unknown weekly

    paid_before = float(contract.total_paid)  # after adding payment to session, use pre-value
    week_from   = int(paid_before // weekly) + 1
    paid_after  = paid_before + payment_amount
    week_to     = int(paid_after // weekly)
    return week_from, week_to


def _overdue(contract: Contract):
    """
    Returns (overdue_weeks: int, overdue_amount: float, weeks_elapsed: int).
    Overdue = weeks elapsed since contract start − weeks already completed.
    """
    if not contract.start_date or contract.status != "active":
        return 0, 0.0, 0

    days_elapsed   = (date.today() - contract.start_date).days
    weeks_elapsed  = max(0, floor(days_elapsed / 7))
    weeks_done     = int(contract.weeks_completed or 0)
    overdue_weeks  = max(0, weeks_elapsed - weeks_done)
    overdue_amount = overdue_weeks * float(contract.weekly_amount or 0)
    return overdue_weeks, overdue_amount, weeks_elapsed


def _overdue_all():
    """List of (contract, overdue_weeks, overdue_amount) for ALL active contracts
    that have at least one overdue week."""
    result = []
    for c in Contract.query.filter_by(status="active").all():
        ow, oa, _ = _overdue(c)
        if ow > 0:
            result.append((c, ow, oa))
    result.sort(key=lambda x: x[1], reverse=True)
    return result


def _build_contracts_json():
    """Build JSON blob of all active contracts keyed by contract_id, for JS."""
    data = {}
    contracts = (Contract.query
                 .filter_by(status="active")
                 .join(Driver, Contract.driver_id == Driver.id)
                 .join(Vehicle, Contract.vehicle_id == Vehicle.id)
                 .all())
    for c in contracts:
        ow, oa, elapsed = _overdue(c)
        data[str(c.id)] = {
            "contract_id":    c.id,
            "driver_id":      c.driver_id,
            "driver_name":    c.driver.full_name,
            "vehicle":        c.vehicle.vehicle_number,
            "vehicle_make":   f"{c.vehicle.manufacturer or ''} {c.vehicle.model or ''}".strip(),
            "total_payable":  float(c.total_payable or 0),
            "total_paid":     round(c.total_paid, 2),
            "outstanding":    round(c.outstanding_balance, 2),
            "weekly_amount":  float(c.weekly_amount or 0),
            "weeks_completed": int(c.weeks_completed or 0),
            "total_weeks":    int(c.total_weeks or 0),
            "overdue_weeks":  ow,
            "overdue_amount": round(oa, 2),
            "weeks_elapsed":  elapsed,
        }
    return data


def _receipt_balance_snapshot(payment: Payment, contract: Contract):
    """
    Compute balance BEFORE and AFTER this specific payment, based on all
    non-archived payments for the contract with id ≤ payment.id.
    Returns (previous_balance, remaining_balance).
    """
    paid_through_this = (
        db.session.query(func.sum(Payment.amount))
        .filter(
            Payment.contract_id == contract.id,
            Payment.is_archived == False,
            Payment.id <= payment.id,
        )
        .scalar() or 0
    )
    remaining = float(contract.total_payable or 0) - float(paid_through_this)
    previous  = remaining + float(payment.amount)
    return previous, remaining


# ─── routes ───────────────────────────────────────────────────────────────────

@payments_bp.route("/")
@login_required
def index():
    search        = request.args.get("q",        "").strip()
    method_filter = request.args.get("method",   "")
    date_from_str = request.args.get("date_from","")
    date_to_str   = request.args.get("date_to",  "")
    page          = request.args.get("page", 1, type=int)

    query = (
        Payment.query
        .join(Driver,   Payment.driver_id   == Driver.id)
        .join(Contract, Payment.contract_id == Contract.id)
        .join(Vehicle,  Contract.vehicle_id == Vehicle.id)
        .filter(Payment.is_archived == False)
        .order_by(Payment.created_at.desc())
    )

    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Driver.full_name.ilike(like),
                Payment.receipt_number.ilike(like),
                Payment.reference.ilike(like),
                Vehicle.vehicle_number.ilike(like),
            )
        )
    if method_filter:
        query = query.filter(Payment.payment_method == method_filter)

    if date_from_str:
        try:
            df = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            query = query.filter(Payment.payment_date >= df)
        except ValueError:
            pass
    if date_to_str:
        try:
            dt = datetime.strptime(date_to_str, "%Y-%m-%d").date()
            query = query.filter(Payment.payment_date <= dt)
        except ValueError:
            pass

    payments = query.paginate(page=page, per_page=25, error_out=False)
    overdue_list = _overdue_all()

    total_amount = sum(float(p.amount) for p in payments.items)

    return render_template(
        "payments/index.html",
        payments=payments,
        overdue_list=overdue_list,
        search=search,
        method_filter=method_filter,
        date_from_str=date_from_str,
        date_to_str=date_to_str,
        total_amount=total_amount,
    )


@payments_bp.route("/receipts")
@login_required
def receipts():
    """Dedicated receipt search — by receipt number, driver, vehicle, or date."""
    q             = request.args.get("q",        "").strip()
    date_from_str = request.args.get("date_from","")
    date_to_str   = request.args.get("date_to",  "")
    page          = request.args.get("page", 1, type=int)

    query = (
        Payment.query
        .join(Driver,   Payment.driver_id   == Driver.id)
        .join(Contract, Payment.contract_id == Contract.id)
        .join(Vehicle,  Contract.vehicle_id == Vehicle.id)
        .order_by(Payment.created_at.desc())
    )

    if q:
        like = f"%{q}%"
        query = query.filter(
            or_(
                Payment.receipt_number.ilike(like),
                Driver.full_name.ilike(like),
                Vehicle.vehicle_number.ilike(like),
            )
        )
    if date_from_str:
        try:
            df = datetime.strptime(date_from_str, "%Y-%m-%d").date()
            query = query.filter(Payment.payment_date >= df)
        except ValueError:
            pass
    if date_to_str:
        try:
            dt = datetime.strptime(date_to_str, "%Y-%m-%d").date()
            query = query.filter(Payment.payment_date <= dt)
        except ValueError:
            pass

    payments = query.paginate(page=page, per_page=30, error_out=False)

    return render_template(
        "payments/receipts.html",
        payments=payments,
        q=q,
        date_from_str=date_from_str,
        date_to_str=date_to_str,
    )


@payments_bp.route("/record", methods=["GET", "POST"])
@login_required
def record():
    # Pre-select a contract if contract_id is in query string
    preselect_contract_id = request.args.get("contract_id", type=int)

    contracts_json = _build_contracts_json()

    # Build list of drivers with active contracts for the dropdown
    active_contracts = (Contract.query
                        .filter_by(status="active")
                        .join(Driver, Contract.driver_id == Driver.id)
                        .order_by(Driver.full_name)
                        .all())

    if request.method == "POST":
        contract_id = request.form.get("contract_id", type=int)
        if not contract_id:
            flash("Please select a contract.", "danger")
            return render_template("payments/record.html",
                                   active_contracts=active_contracts,
                                   contracts_json=json.dumps(contracts_json),
                                   preselect_contract_id=preselect_contract_id,
                                   today=date.today(), form=request.form)

        contract = Contract.query.get_or_404(contract_id)
        if contract.status != "active":
            flash("Payments can only be recorded against active contracts.", "danger")
            return redirect(url_for("payments.record"))

        # ── Parse form fields ────────────────────────────────────────────────
        amount_str = request.form.get("amount", "0").replace(",", "").strip()
        try:
            amount = float(amount_str)
        except ValueError:
            amount = 0.0

        if amount <= 0:
            flash("Payment amount must be greater than zero.", "danger")
            return render_template("payments/record.html",
                                   active_contracts=active_contracts,
                                   contracts_json=json.dumps(contracts_json),
                                   preselect_contract_id=contract_id,
                                   today=date.today(), form=request.form)

        outstanding = contract.outstanding_balance
        if amount > outstanding > 0:
            flash(
                f"Payment of ₦{amount:,.0f} exceeds the outstanding balance of "
                f"₦{outstanding:,.0f} for this contract. Please enter an amount "
                f"up to the outstanding balance, or record it in smaller instalments.",
                "danger",
            )
            return render_template("payments/record.html",
                                   active_contracts=active_contracts,
                                   contracts_json=json.dumps(contracts_json),
                                   preselect_contract_id=contract_id,
                                   today=date.today(), form=request.form)

        pay_date_str = request.form.get("payment_date", str(date.today()))
        try:
            pay_date = datetime.strptime(pay_date_str, "%Y-%m-%d").date()
        except ValueError:
            pay_date = date.today()

        pay_time_str = request.form.get("payment_time", "").strip()
        pay_time = None
        if pay_time_str:
            try:
                parts = pay_time_str.split(":")
                pay_time = dtime(int(parts[0]), int(parts[1]))
            except Exception:
                pay_time = None

        # ── Compute week coverage BEFORE adding this payment ─────────────────
        week_from, week_to = _compute_week_coverage(contract, amount)

        # ── Create payment record ─────────────────────────────────────────────
        payment = Payment(
            contract_id    = contract.id,
            driver_id      = contract.driver_id,
            amount         = amount,
            payment_date   = pay_date,
            payment_time   = pay_time,
            week_from      = week_from,
            week_to        = week_to,
            week_number    = week_from,  # legacy compat
            payment_method = request.form.get("payment_method", "cash"),
            bank_name      = request.form.get("bank_name",  "").strip() or None,
            pos_terminal   = request.form.get("pos_terminal","").strip() or None,
            sender         = request.form.get("sender",     "").strip() or None,
            receiver       = request.form.get("receiver",   "").strip() or None,
            reference      = request.form.get("reference",  "").strip() or None,
            notes          = request.form.get("notes",      "").strip() or None,
            recorded_by    = current_user.id,
        )

        db.session.add(payment)
        db.session.flush()  # get payment.id

        # ── Assign globally-unique, never-reused receipt number ───────────────
        payment.receipt_number = _generate_receipt(payment)

        # ── Recalculate contract progress ─────────────────────────────────────
        contract.recalculate_weeks()

        # ── Audit log ─────────────────────────────────────────────────────────
        _log("RECORD_PAYMENT", payment,
             f"Weeks: {payment.week_range_display if hasattr(payment, 'week_range_display') else week_from}")
        db.session.commit()

        flash(
            f"Payment of ₦{amount:,.0f} recorded. "
            f"Receipt: {payment.receipt_number}",
            "success",
        )
        # Redirect to view with flag so the page highlights receipt buttons
        return redirect(url_for("payments.view", payment_id=payment.id, just_recorded=1))

    return render_template(
        "payments/record.html",
        active_contracts=active_contracts,
        contracts_json=json.dumps(contracts_json),
        preselect_contract_id=preselect_contract_id,
        today=date.today(),
        form={},
    )


@payments_bp.route("/<int:payment_id>")
@login_required
def view(payment_id):
    payment      = Payment.query.get_or_404(payment_id)
    contract     = payment.contract
    ow, oa, _    = _overdue(contract)
    just_recorded = request.args.get("just_recorded", 0, type=int)
    return render_template(
        "payments/view.html",
        payment=payment,
        contract=contract,
        overdue_weeks=ow,
        overdue_amount=oa,
        just_recorded=just_recorded,
    )


@payments_bp.route("/<int:payment_id>/receipt")
@login_required
def receipt(payment_id):
    payment  = Payment.query.get_or_404(payment_id)
    contract = payment.contract

    previous_balance, remaining_balance = _receipt_balance_snapshot(payment, contract)

    from backend.models.user import User
    recorder = User.query.get(payment.recorded_by) if payment.recorded_by else None

    # Audit: receipt was viewed / reprinted
    _log("VIEW_RECEIPT", payment, "Receipt viewed in browser.")
    db.session.commit()

    return render_template(
        "payments/receipt.html",
        payment=payment,
        contract=contract,
        printed_at=datetime.utcnow(),
        previous_balance=previous_balance,
        remaining_balance=remaining_balance,
        recorder=recorder,
    )


@payments_bp.route("/<int:payment_id>/receipt/pdf")
@login_required
def receipt_pdf(payment_id):
    """Generate and download a professional PDF receipt."""
    payment  = Payment.query.get_or_404(payment_id)
    contract = payment.contract

    previous_balance, remaining_balance = _receipt_balance_snapshot(payment, contract)

    from backend.models.user import User
    recorder = User.query.get(payment.recorded_by) if payment.recorded_by else None

    html = render_template(
        "payments/receipt_pdf.html",
        payment=payment,
        contract=contract,
        printed_at=datetime.utcnow(),
        previous_balance=previous_balance,
        remaining_balance=remaining_balance,
        recorder=recorder,
    )

    try:
        from xhtml2pdf import pisa
        pdf_buffer = BytesIO()
        pisa.CreatePDF(html, dest=pdf_buffer, base_url=request.url_root)
        pdf_buffer.seek(0)
        pdf_bytes = pdf_buffer.read()
    except Exception as e:
        flash(f"PDF generation failed: {e}", "danger")
        return redirect(url_for("payments.receipt", payment_id=payment_id))

    # Audit: PDF receipt downloaded
    _log("PRINT_RECEIPT", payment, "PDF receipt downloaded.")
    db.session.commit()

    filename = f"Receipt-{payment.receipt_number or payment.id}.pdf"
    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@payments_bp.route("/<int:payment_id>/void", methods=["POST"])
@login_required
def void(payment_id):
    payment  = Payment.query.get_or_404(payment_id)
    contract = payment.contract

    if payment.is_archived:
        flash("This payment has already been voided.", "info")
        return redirect(url_for("payments.view", payment_id=payment_id))

    payment.is_archived = True
    contract.recalculate_weeks()  # recompute without this payment

    _log("VOID_PAYMENT", payment, "Payment voided — excluded from totals.")
    db.session.commit()

    flash(
        f"Payment {payment.receipt_number} has been voided. "
        f"Contract balance has been updated.",
        "warning",
    )
    return redirect(url_for("payments.history", contract_id=contract.id))


@payments_bp.route("/history/<int:contract_id>")
@login_required
def history(contract_id):
    contract = Contract.query.get_or_404(contract_id)
    page     = request.args.get("page", 1, type=int)
    printable = request.args.get("print", "") == "1"

    payments_q = (
        Payment.query
        .filter_by(contract_id=contract_id, is_archived=False)
        .order_by(Payment.payment_date.asc(), Payment.created_at.asc())
    )

    if printable:
        all_payments = payments_q.all()
        ow, oa, _ = _overdue(contract)
        return render_template(
            "payments/history.html",
            contract=contract,
            payments=all_payments,
            overdue_weeks=ow,
            overdue_amount=oa,
            printable=True,
            printed_at=datetime.utcnow(),
        )

    payments_pg = payments_q.paginate(page=page, per_page=30, error_out=False)
    ow, oa, _ = _overdue(contract)
    return render_template(
        "payments/history.html",
        contract=contract,
        payments=payments_pg,
        overdue_weeks=ow,
        overdue_amount=oa,
        printable=False,
        printed_at=None,
    )


@payments_bp.route("/overdue")
@login_required
def overdue():
    overdue_list = _overdue_all()
    total_overdue_amount = sum(oa for _, _, oa in overdue_list)
    return render_template(
        "payments/overdue.html",
        overdue_list=overdue_list,
        total_overdue_amount=total_overdue_amount,
    )


@payments_bp.route("/api/contract-info")
@login_required
def api_contract_info():
    """Return contract JSON for the record-payment JS widget."""
    contracts_json = _build_contracts_json()
    return jsonify(contracts_json)
