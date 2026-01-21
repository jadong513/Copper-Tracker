# Copper Price Tracker

A web-based application for tracking live copper prices with a focus on 16oz flat copper sheet and coil pricing.

## Features

- **Live Price Display**: Real-time COMEX copper futures prices
- **Calculated Pricing**: Automatic calculation of 16oz sheet and coil prices based on raw copper + fabrication markup
- **Historical Charts**: View price history from 1 day to 1 year
- **Price Alerts**: Set alerts for when prices go above or below thresholds
- **Auto-refresh**: Configurable automatic price updates

## Data Source

This application uses **Yahoo Finance** to fetch COMEX Copper Futures (HG=F) prices. The raw copper price is then used to calculate estimated sheet and coil prices using a configurable fabrication markup.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/jadong513/Copper-Tracker.git
   cd Copper-Tracker
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Create a `.env` file for configuration:
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. Run the application:
   ```bash
   python app.py
   ```

6. Open your browser to `http://localhost:5000`

## Configuration

Configuration can be done via environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `SECRET_KEY` | `dev-secret-key...` | Flask secret key |
| `DATABASE_URL` | `sqlite:///copper_prices.db` | Database connection string |
| `UPDATE_INTERVAL` | `15` | Background price fetch interval (minutes) |
| `FABRICATION_MARKUP` | `35` | Markup percentage for sheet/coil pricing |

## Price Calculations

- **Raw Copper**: Direct COMEX copper futures price (per pound)
- **16oz Sheet**: Raw price + fabrication markup (default 35%)
- **Coil**: Raw price + fabrication markup - 5% (coils typically cost less)

The fabrication markup can be adjusted to match your supplier's actual pricing.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/price/current` | GET | Current copper prices |
| `/api/price/history?period=1mo` | GET | Historical prices |
| `/api/price/intraday` | GET | Today's intraday prices |
| `/api/alerts` | GET | List all price alerts |
| `/api/alerts` | POST | Create new alert |
| `/api/alerts/<id>` | DELETE | Delete an alert |
| `/api/alerts/<id>/toggle` | POST | Toggle alert active status |

## Tech Stack

- **Backend**: Python, Flask, SQLAlchemy
- **Database**: SQLite
- **Data Source**: Yahoo Finance (yfinance)
- **Frontend**: Bootstrap 5, Chart.js
- **Background Jobs**: APScheduler

## License

MIT License
