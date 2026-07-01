from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required
from backend.extensions import db
from backend.models.vehicle import Vehicle

vehicles_bp = Blueprint("vehicles", __name__)


@vehicles_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "")
    status = request.args.get("status", "")
    page = request.args.get("page", 1, type=int)

    query = Vehicle.query
    if status:
        query = query.filter_by(status=status)
    if search:
        query = query.filter(
            db.or_(
                Vehicle.vehicle_number.ilike(f"%{search}%"),
                Vehicle.reg_number.ilike(f"%{search}%"),
                Vehicle.model.ilike(f"%{search}%"),
            )
        )
    vehicles = query.order_by(Vehicle.id.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("vehicles/index.html", vehicles=vehicles, search=search, status=status)


@vehicles_bp.route("/add", methods=["GET", "POST"])
@login_required
def add():
    if request.method == "POST":
        vehicle = Vehicle(
            vehicle_number=request.form["vehicle_number"],
            reg_number=request.form.get("reg_number"),
            engine_number=request.form.get("engine_number"),
            chassis_number=request.form.get("chassis_number"),
            model=request.form.get("model"),
            manufacturer=request.form.get("manufacturer"),
            year=request.form.get("year") or None,
            purchase_price=request.form.get("purchase_price") or 0,
            notes=request.form.get("notes"),
        )
        db.session.add(vehicle)
        db.session.commit()
        flash(f"Vehicle '{vehicle.vehicle_number}' added successfully.", "success")
        return redirect(url_for("vehicles.index"))
    return render_template("vehicles/add.html")


@vehicles_bp.route("/<int:vehicle_id>")
@login_required
def view(vehicle_id):
    vehicle = Vehicle.query.get_or_404(vehicle_id)
    return render_template("vehicles/view.html", vehicle=vehicle)
