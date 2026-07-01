from datetime import datetime
from backend.extensions import db


class Driver(db.Model):
    __tablename__ = "drivers"

    id = db.Column(db.Integer, primary_key=True)

    # Personal info
    full_name = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    address = db.Column(db.Text, nullable=True)
    photo_path = db.Column(db.String(255), nullable=True)
    national_id = db.Column(db.String(50), nullable=True)

    # Next of kin
    nok_name = db.Column(db.String(120), nullable=True)
    nok_phone = db.Column(db.String(20), nullable=True)
    nok_relationship = db.Column(db.String(50), nullable=True)
    nok_address = db.Column(db.Text, nullable=True)

    # Witness 1
    witness1_name = db.Column(db.String(120), nullable=True)
    witness1_phone = db.Column(db.String(20), nullable=True)
    witness1_address = db.Column(db.Text, nullable=True)

    # Witness 2
    witness2_name = db.Column(db.String(120), nullable=True)
    witness2_phone = db.Column(db.String(20), nullable=True)
    witness2_address = db.Column(db.Text, nullable=True)

    # Guarantor 1
    guarantor1_name = db.Column(db.String(120), nullable=True)
    guarantor1_phone = db.Column(db.String(20), nullable=True)
    guarantor1_address = db.Column(db.Text, nullable=True)

    # Guarantor 2
    guarantor2_name = db.Column(db.String(120), nullable=True)
    guarantor2_phone = db.Column(db.String(20), nullable=True)
    guarantor2_address = db.Column(db.Text, nullable=True)

    # Status & dates
    status = db.Column(db.String(20), default="active")  # active, archived, suspended
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)
    date_archived = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    contracts = db.relationship("Contract", backref="driver", lazy="dynamic")
    payments = db.relationship("Payment", backref="driver", lazy="dynamic")
    expenses = db.relationship("Expense", backref="driver", lazy="dynamic")

    @property
    def active_contract(self):
        return self.contracts.filter_by(status="active").first()

    @property
    def total_paid(self):
        return sum(p.amount for p in self.payments.filter_by(is_archived=False))

    @property
    def total_outstanding(self):
        contract = self.active_contract
        if contract:
            return contract.total_payable - self.total_paid
        return 0

    def __repr__(self):
        return f"<Driver {self.full_name}>"
