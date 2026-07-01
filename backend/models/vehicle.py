"""
Vehicle — core fleet asset record.

Fields follow the business requirements for a Nigerian hire-purchase transport
company. The `vehicle_number` column doubles as the government-issued plate
number (most operators use the plate as the fleet identifier).

Status values
-------------
available   — free, no active hire-purchase contract
assigned    — currently under an active hire-purchase contract
maintenance — off the road for servicing / repairs
archived    — soft-deleted; record preserved forever
"""

from datetime import datetime
from backend.extensions import db


class Vehicle(db.Model):
    __tablename__ = "vehicles"

    id = db.Column(db.Integer, primary_key=True)

    # ── Identification ────────────────────────────────────────────────────────
    vehicle_number = db.Column(db.String(50), unique=True, nullable=False)   # plate / fleet no.
    reg_number     = db.Column(db.String(50), unique=True, nullable=True)    # FRSC registration
    engine_number  = db.Column(db.String(100), nullable=True)
    chassis_number = db.Column(db.String(100), nullable=True)

    # ── Description ───────────────────────────────────────────────────────────
    manufacturer   = db.Column(db.String(100), nullable=True)   # Toyota, Nissan, etc.
    model          = db.Column(db.String(100), nullable=True)   # Corolla, Hiace, etc.
    year           = db.Column(db.Integer, nullable=True)
    color          = db.Column(db.String(50), nullable=True)

    # ── Financials ────────────────────────────────────────────────────────────
    purchase_price = db.Column(db.Numeric(15, 2), default=0)
    purchase_date  = db.Column(db.Date, nullable=True)
    delivery_date  = db.Column(db.Date, nullable=True)

    # ── Operational ───────────────────────────────────────────────────────────
    current_mileage          = db.Column(db.Integer, nullable=True)
    insurance_expiry         = db.Column(db.Date, nullable=True)
    road_worthiness_expiry   = db.Column(db.Date, nullable=True)

    # ── Status & lifecycle ────────────────────────────────────────────────────
    # Allowed: available | assigned | maintenance | archived
    status          = db.Column(db.String(20), default="available", nullable=False)
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    date_archived   = db.Column(db.DateTime, nullable=True)
    notes           = db.Column(db.Text, nullable=True)

    # ── Relationships ─────────────────────────────────────────────────────────
    contracts = db.relationship("Contract", backref="vehicle", lazy="dynamic")
    expenses  = db.relationship("Expense",  backref="vehicle", lazy="dynamic")
    events    = db.relationship(
        "VehicleEvent",
        backref="vehicle",
        lazy="dynamic",
        cascade="all, delete-orphan",
        order_by="VehicleEvent.event_date.desc()",
    )

    # ── Computed properties ───────────────────────────────────────────────────

    @property
    def active_contract(self):
        return self.contracts.filter_by(status="active").first()

    @property
    def current_driver(self):
        contract = self.active_contract
        return contract.driver if contract else None

    @property
    def display_name(self):
        """Human-friendly short name: plate + make/model."""
        parts = [self.vehicle_number]
        if self.manufacturer or self.model:
            desc = " ".join(filter(None, [self.manufacturer, self.model]))
            parts.append(f"({desc})")
        return " ".join(parts)

    def __repr__(self):
        return f"<Vehicle {self.vehicle_number}>"
