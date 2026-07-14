from flask import Flask
from backend.extensions import db, login_manager
from backend.config import config


def create_app(config_name="default"):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config[config_name])

    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    # ── Blueprints ────────────────────────────────────────────────────────────
    from backend.routes.auth      import auth_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.drivers   import drivers_bp
    from backend.routes.vehicles  import vehicles_bp
    from backend.routes.contracts import contracts_bp
    from backend.routes.payments  import payments_bp
    from backend.routes.reports   import reports_bp
    from backend.routes.archives  import archives_bp
    from backend.routes.developer import developer_bp
    from backend.routes.settings  import settings_bp
    from backend.routes.expenses  import expenses_bp
    from backend.routes.audit     import audit_bp
    from backend.routes.capital   import capital_bp
    from backend.routes.admin     import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(drivers_bp,   url_prefix="/drivers")
    app.register_blueprint(vehicles_bp,  url_prefix="/vehicles")
    app.register_blueprint(contracts_bp, url_prefix="/contracts")
    app.register_blueprint(payments_bp,  url_prefix="/payments")
    app.register_blueprint(expenses_bp,  url_prefix="/expenses")
    app.register_blueprint(reports_bp,   url_prefix="/reports")
    app.register_blueprint(archives_bp,  url_prefix="/archives")
    app.register_blueprint(developer_bp, url_prefix="/developer")
    app.register_blueprint(settings_bp,  url_prefix="/settings")
    app.register_blueprint(audit_bp,     url_prefix="/audit-log")
    app.register_blueprint(capital_bp,   url_prefix="/capital")
    app.register_blueprint(admin_bp,     url_prefix="/admin")

    # ── Flask-Login user loader ───────────────────────────────────────────────
    from backend.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # ── Global template context ───────────────────────────────────────────────
    from backend.models.settings import BusinessSettings, AppPreferences

    @app.context_processor
    def inject_global_settings():
        try:
            biz   = BusinessSettings.get()
            prefs = AppPreferences.get()
        except Exception:
            biz   = None
            prefs = None
        return dict(biz=biz, app_prefs=prefs)

    # ── Custom Jinja2 filters ─────────────────────────────────────────────────
    import markupsafe

    @app.template_filter("nl2br")
    def nl2br_filter(value):
        if not value:
            return ""
        escaped = markupsafe.escape(value)
        return markupsafe.Markup(str(escaped).replace("\n", "<br>\n"))

    # ── DB setup ──────────────────────────────────────────────────────────────
    with app.app_context():
        # Import all models so SQLAlchemy sees them before create_all()
        from backend.models import (          # noqa: F401
            user, driver, vehicle, vehicle_event,
            contract, payment, expense, audit, capital, settings,
            receipt_seq,
        )
        db.create_all()
        _run_migrations()
        _seed_defaults()
        _seed_settings()
        _seed_receipt_seq()

    return app


def _run_migrations():
    """
    Safe, additive schema migrations — run on every startup.
    Every ALTER TABLE uses IF NOT EXISTS so it is idempotent.
    """
    from sqlalchemy import text

    migrations = [
        # ── drivers ──────────────────────────────────────────────────────────
        "ALTER TABLE drivers ADD COLUMN IF NOT EXISTS license_number VARCHAR(50)",

        # ── vehicles ─────────────────────────────────────────────────────────
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS color VARCHAR(50)",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS current_mileage INTEGER",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS insurance_expiry DATE",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS road_worthiness_expiry DATE",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS date_registered TIMESTAMP WITHOUT TIME ZONE DEFAULT NOW()",
        "ALTER TABLE vehicles ADD COLUMN IF NOT EXISTS date_archived TIMESTAMP WITHOUT TIME ZONE",

        # ── contracts ────────────────────────────────────────────────────────
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS purchase_date DATE",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS delivery_date DATE",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS date_completed TIMESTAMP WITHOUT TIME ZONE",
        "ALTER TABLE contracts ADD COLUMN IF NOT EXISTS date_archived TIMESTAMP WITHOUT TIME ZONE",

        # ── expenses ─────────────────────────────────────────────────────────
        "ALTER TABLE expenses ADD COLUMN IF NOT EXISTS contract_id INTEGER REFERENCES contracts(id)",

        # ── payments ─────────────────────────────────────────────────────────
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS receipt_number VARCHAR(30)",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS week_from INTEGER",
        "ALTER TABLE payments ADD COLUMN IF NOT EXISTS week_to INTEGER",

        # ── users ────────────────────────────────────────────────────────────
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS display_name VARCHAR(120)",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_photo VARCHAR(255)",
    ]

    with db.engine.connect() as conn:
        for stmt in migrations:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                # Roll back so one failed/unsupported statement (e.g. on Postgres,
                # which aborts the whole transaction on error) doesn't silently
                # block every later migration in this loop.
                conn.rollback()


def _seed_defaults():
    from backend.models.user import User

    if User.query.count() == 0:
        owner = User(username="owner", email="owner@thms.local", role="owner")
        owner.set_password("owner123")
        dev = User(username="developer", email="dev@thms.local", role="developer")
        dev.set_password("dev123")
        db.session.add_all([owner, dev])
        db.session.commit()


def _seed_settings():
    from backend.models.settings import BusinessSettings, AppPreferences
    BusinessSettings.get()
    AppPreferences.get()


def _seed_receipt_seq():
    """Ensure the single receipt-sequence row exists (creates it if absent)."""
    from backend.models.receipt_seq import ReceiptSequence
    if ReceiptSequence.query.first() is None:
        db.session.add(ReceiptSequence(last_seq=0))
        db.session.commit()
