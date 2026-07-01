from flask import Blueprint, render_template, request
from flask_login import login_required
from backend.models.driver import Driver
from backend.models.contract import Contract

archives_bp = Blueprint("archives", __name__)


@archives_bp.route("/")
@login_required
def index():
    search = request.args.get("q", "")
    page = request.args.get("page", 1, type=int)

    query = Driver.query.filter(Driver.status == "archived")
    if search:
        query = query.filter(Driver.full_name.ilike(f"%{search}%"))
    drivers = query.order_by(Driver.date_archived.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template("archives/index.html", drivers=drivers, search=search)
