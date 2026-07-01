from flask import Flask
from backend.extensions import db, login_manager
from backend.config import config


def create_app(config_name="default"):
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config.from_object(config[config_name])

    # Ensure upload folder exists
    import os
    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.dashboard import dashboard_bp
    from backend.routes.drivers import drivers_bp
    from backend.routes.vehicles import vehicles_bp
    from backend.routes.payments import payments_bp
    from backend.routes.reports import reports_bp
    from backend.routes.archives import archives_bp
    from backend.routes.developer import developer_bp
    from backend.routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(drivers_bp, url_prefix="/drivers")
    app.register_blueprint(vehicles_bp, url_prefix="/vehicles")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(reports_bp, url_prefix="/reports")
    app.register_blueprint(archives_bp, url_prefix="/archives")
    app.register_blueprint(developer_bp, url_prefix="/developer")
    app.register_blueprint(settings_bp, url_prefix="/settings")

    # User loader for Flask-Login
    from backend.models.user import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Create tables and seed default users on first run
    with app.app_context():
        db.create_all()
        _seed_defaults()

    return app


def _seed_defaults():
    from backend.models.user import User

    if User.query.count() == 0:
        owner = User(username="owner", email="owner@thms.local", role="owner")
        owner.set_password("owner123")
        dev = User(username="developer", email="dev@thms.local", role="developer")
        dev.set_password("dev123")
        db.session.add_all([owner, dev])
        db.session.commit()
