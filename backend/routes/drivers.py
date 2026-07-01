from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from backend.extensions import db
from backend.models.driver import Driver

drivers_bp = Blueprint("drivers", __name__)


@drivers_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "")
    status = request.args.get("status", "active")
    page = request.args.get("page", 1, type=int)

    query = Driver.query
    if status and status != "all":
        query = query.filter_by(status=status)
    if search:
        query = query.filter(Driver.full_name.ilike(f"%{search}%"))

    drivers = query.order_by(Driver.date_registered.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("drivers/index.html", drivers=drivers, search=search, status=status)


@drivers_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        driver = Driver(
            full_name=request.form["full_name"],
            phone=request.form["phone"],
            address=request.form.get("address"),
            national_id=request.form.get("national_id"),
            nok_name=request.form.get("nok_name"),
            nok_phone=request.form.get("nok_phone"),
            nok_relationship=request.form.get("nok_relationship"),
            nok_address=request.form.get("nok_address"),
            notes=request.form.get("notes"),
        )
        db.session.add(driver)
        db.session.commit()
        flash(f"Driver '{driver.full_name}' added successfully.", "success")
        return redirect(url_for("drivers.index"))
    return render_template("drivers/add.html")


@drivers_bp.route("/<int:driver_id>")
@login_required
def view(driver_id):
    driver = Driver.query.get_or_404(driver_id)
    active_contract = driver.active_contract
    recent_payments = (
        driver.payments
        .filter_by(is_archived=False)
        .order_by(driver.payments.property.mapper.class_.created_at.desc())
        .limit(15)
        .all()
    )
    return render_template(
        "drivers/view.html",
        driver=driver,
        active_contract=active_contract,
        recent_payments=recent_payments,
    )
