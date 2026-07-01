"""
VehicleEvent — immutable timeline entry for a vehicle.

Every significant event (registered, status changes, maintenance, archiving, etc.)
is written here as a permanent record. Events are never deleted; they form the
complete history / audit trail for each vehicle.

Fields
------
vehicle_id   FK to vehicles.id
event_type   machine-readable tag: 'registered', 'assigned', 'returned',
             'maintenance_start', 'maintenance_end', 'repair',
             'contract_completed', 'archived', 'restored', 'status_change', 'note'
title        short human-readable summary
description  optional longer detail
event_date   when the real-world event happened (defaults to now)
created_by   username of the logged-in user who triggered this entry
created_at   server timestamp when the row was written
"""

from datetime import datetime
from backend.extensions import db


class VehicleEvent(db.Model):
    __tablename__ = "vehicle_events"

    id = db.Column(db.Integer, primary_key=True)

    vehicle_id = db.Column(
        db.Integer, db.ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False
    )

    event_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)

    event_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    created_by = db.Column(db.String(80), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<VehicleEvent {self.event_type} vehicle={self.vehicle_id}>"

    # ── convenience ────────────────────────────────────────────────────────────

    @property
    def icon(self):
        """Bootstrap-icon class for this event type."""
        return {
            "registered":        "bi-plus-circle-fill text-success",
            "assigned":          "bi-person-fill text-primary",
            "returned":          "bi-person-dash text-warning",
            "maintenance_start": "bi-tools text-warning",
            "maintenance_end":   "bi-check2-circle text-success",
            "repair":            "bi-wrench-adjustable text-secondary",
            "contract_completed":"bi-trophy-fill text-success",
            "archived":          "bi-archive-fill text-secondary",
            "restored":          "bi-arrow-counterclockwise text-info",
            "status_change":     "bi-arrow-left-right text-info",
            "note":              "bi-sticky-fill text-warning",
        }.get(self.event_type, "bi-circle text-muted")
