"""Copper Price Tracker - Flask Application."""

from flask import Flask, render_template, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import atexit

from config import Config
from models import db, PriceRecord, PriceAlert
from services.price_service import CopperPriceService

app = Flask(__name__)
app.config.from_object(Config)

# Initialize database
db.init_app(app)

# Initialize price service
price_service = CopperPriceService()

# Triggered alerts storage (in-memory for simplicity)
triggered_alerts = []


def fetch_and_store_price():
    """Background job to fetch and store current price."""
    with app.app_context():
        prices = price_service.get_current_price()
        if prices:
            record = PriceRecord(
                raw_price=prices['raw_price'],
                sheet_price=prices['sheet_price'],
                coil_price=prices['coil_price']
            )
            db.session.add(record)
            db.session.commit()

            # Check alerts
            check_alerts(prices)


def check_alerts(prices):
    """Check if any alerts should be triggered."""
    global triggered_alerts
    alerts = PriceAlert.query.filter_by(is_active=True).all()

    for alert in alerts:
        if alert.price_type == 'raw':
            current = prices['raw_price']
        elif alert.price_type == 'sheet':
            current = prices['sheet_price']
        else:
            current = prices['coil_price']

        if alert.check_condition(current):
            alert.triggered_at = datetime.utcnow()
            alert.notification_sent = True
            triggered_alerts.append({
                'id': alert.id,
                'message': f"Alert: {alert.price_type.title()} price is {alert.condition} ${alert.threshold:.2f} (Current: ${current:.2f})",
                'timestamp': datetime.utcnow().isoformat()
            })
            db.session.commit()


# Routes
@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('index.html')


@app.route('/api/price/current')
def get_current_price():
    """Get current copper prices."""
    prices = price_service.get_current_price()
    if prices:
        change = price_service.get_price_change()
        prices['change'] = change
        return jsonify(prices)
    return jsonify({'error': 'Unable to fetch price'}), 500


@app.route('/api/price/history')
def get_price_history():
    """Get historical prices from database."""
    period = request.args.get('period', '1mo')

    # Get from Yahoo Finance for chart
    records = price_service.get_historical_prices(period)

    return jsonify({
        'period': period,
        'records': records
    })


@app.route('/api/price/intraday')
def get_intraday_prices():
    """Get intraday prices."""
    records = price_service.get_intraday_prices()
    return jsonify({'records': records})


@app.route('/api/price/stored')
def get_stored_prices():
    """Get prices stored in local database."""
    limit = request.args.get('limit', 100, type=int)
    records = PriceRecord.query.order_by(PriceRecord.timestamp.desc()).limit(limit).all()
    return jsonify([r.to_dict() for r in records])


@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """Get all price alerts."""
    alerts = PriceAlert.query.order_by(PriceAlert.created_at.desc()).all()
    return jsonify([a.to_dict() for a in alerts])


@app.route('/api/alerts', methods=['POST'])
def create_alert():
    """Create a new price alert."""
    data = request.json
    alert = PriceAlert(
        price_type=data['price_type'],
        condition=data['condition'],
        threshold=float(data['threshold'])
    )
    db.session.add(alert)
    db.session.commit()
    return jsonify(alert.to_dict()), 201


@app.route('/api/alerts/<int:alert_id>', methods=['DELETE'])
def delete_alert(alert_id):
    """Delete a price alert."""
    alert = PriceAlert.query.get_or_404(alert_id)
    db.session.delete(alert)
    db.session.commit()
    return jsonify({'message': 'Alert deleted'})


@app.route('/api/alerts/<int:alert_id>/toggle', methods=['POST'])
def toggle_alert(alert_id):
    """Toggle alert active status."""
    alert = PriceAlert.query.get_or_404(alert_id)
    alert.is_active = not alert.is_active
    db.session.commit()
    return jsonify(alert.to_dict())


@app.route('/api/alerts/triggered')
def get_triggered_alerts():
    """Get recently triggered alerts."""
    global triggered_alerts
    alerts = triggered_alerts.copy()
    triggered_alerts = []  # Clear after reading
    return jsonify(alerts)


@app.route('/api/settings', methods=['GET'])
def get_settings():
    """Get current settings."""
    return jsonify({
        'fabrication_markup': Config.FABRICATION_MARKUP_PERCENT,
        'update_interval': Config.PRICE_UPDATE_INTERVAL_MINUTES
    })


# Initialize database and scheduler
with app.app_context():
    db.create_all()

# Set up background scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=fetch_and_store_price,
    trigger='interval',
    minutes=Config.PRICE_UPDATE_INTERVAL_MINUTES
)
scheduler.start()

# Shut down scheduler on exit
atexit.register(lambda: scheduler.shutdown())


if __name__ == '__main__':
    # Fetch initial price
    with app.app_context():
        fetch_and_store_price()

    app.run(debug=True, host='0.0.0.0', port=5000)
