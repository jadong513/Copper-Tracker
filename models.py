"""Database models for Copper Price Tracker."""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class PriceRecord(db.Model):
    """Historical copper price record."""

    __tablename__ = 'price_records'

    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    raw_price = db.Column(db.Float, nullable=False)  # COMEX copper price per lb
    sheet_price = db.Column(db.Float, nullable=False)  # Calculated 16oz sheet price
    coil_price = db.Column(db.Float, nullable=False)  # Calculated coil price
    source = db.Column(db.String(50), default='COMEX')

    def to_dict(self):
        """Convert record to dictionary."""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'raw_price': self.raw_price,
            'sheet_price': self.sheet_price,
            'coil_price': self.coil_price,
            'source': self.source
        }


class PriceAlert(db.Model):
    """Price alert configuration."""

    __tablename__ = 'price_alerts'

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    price_type = db.Column(db.String(20), nullable=False)  # 'raw', 'sheet', 'coil'
    condition = db.Column(db.String(10), nullable=False)  # 'above', 'below'
    threshold = db.Column(db.Float, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    triggered_at = db.Column(db.DateTime, nullable=True)
    notification_sent = db.Column(db.Boolean, default=False)

    def to_dict(self):
        """Convert alert to dictionary."""
        return {
            'id': self.id,
            'created_at': self.created_at.isoformat(),
            'price_type': self.price_type,
            'condition': self.condition,
            'threshold': self.threshold,
            'is_active': self.is_active,
            'triggered_at': self.triggered_at.isoformat() if self.triggered_at else None,
            'notification_sent': self.notification_sent
        }

    def check_condition(self, current_price):
        """Check if alert condition is met."""
        if self.condition == 'above':
            return current_price > self.threshold
        elif self.condition == 'below':
            return current_price < self.threshold
        return False
