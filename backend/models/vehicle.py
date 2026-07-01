from datetime import datetime
from backend.extensions import db


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_number = db.Column(db.String(50), unique=True, nullable=False)
    reg_number = db.Column(db.String(50), unique=True, nullable=True)
    engine_number = db.Column(db.String(100), nullable=True)
    chassis_number = db.Column(db.String(100), nullable=True)
    model = db.Column(db.String(100), nullable=True)
    manufacturer = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)

    purchase_date = db.Column(db.Date, nullable=True)
    delivery_date = db.Column(db.Date, nullable=True)
    purchase_price = db.Column(db.Numeric(15, 2), default=0)

    # Status: available, assigned, archived, maintenance
    status = db.Column(db.String(20), default="available")
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    contracts = db.relationship("Contract", backref="vehicle", lazy="dynamic")
    expenses = db.relationship("Expense", backref="vehicle", lazy="dynamic")

    @property
    def active_contract(self):
        return self.contracts.filter_by(status="active").first()

    @property
    def current_driver(self):
        contract = self.active_contract
        if contract:
            return contract.driver
        return None

    def __repr__(self):
        return f"<Vehicle {self.vehicle_number}>"
