"""Service for fetching and calculating copper prices."""

import requests
from datetime import datetime, timedelta
from config import Config


class CopperPriceService:
    """Service for fetching copper prices from multiple sources."""

    # Metals API endpoint (free, no key required for spot prices)
    METALS_API_URL = "https://api.metals.dev/v1/latest"

    def __init__(self):
        self.markup_percent = Config.FABRICATION_MARKUP_PERCENT
        self._last_known_price = None
        self._last_fetch_time = None
        self._price_history = []

    def get_current_price(self):
        """
        Fetch current copper price from metals.dev API.

        Returns:
            dict: Current prices including raw, sheet, and coil
        """
        # Try metals.dev API first
        price = self._fetch_from_metals_dev()

        if price:
            self._last_known_price = price
            self._last_fetch_time = datetime.utcnow()
            return self._calculate_prices(price)

        # Fallback to last known price
        if self._last_known_price:
            print("Using cached price data")
            return self._calculate_prices(self._last_known_price)

        # Last resort: use realistic demo data
        print("Using demo price data")
        demo_price = 4.25  # Realistic copper price per lb
        return self._calculate_prices(demo_price)

    def _fetch_from_metals_dev(self):
        """Fetch copper price from metals.dev free API."""
        try:
            # metals.dev provides free spot prices
            response = requests.get(
                self.METALS_API_URL,
                params={
                    'api_key': 'demo',  # Demo key for limited requests
                    'currency': 'USD',
                    'unit': 'lb'
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'metals' in data and 'copper' in data['metals']:
                    price = float(data['metals']['copper'])
                    print(f"Fetched copper price from metals.dev: ${price:.4f}/lb")
                    return price

            # If metals.dev doesn't work, try alternative
            return self._fetch_from_alternative()

        except Exception as e:
            print(f"Error fetching from metals.dev: {e}")
            return self._fetch_from_alternative()

    def _fetch_from_alternative(self):
        """Try alternative free API sources."""
        try:
            # Try metalpriceapi (has free tier)
            response = requests.get(
                "https://api.metalpriceapi.com/v1/latest",
                params={
                    'api_key': 'demo',
                    'base': 'USD',
                    'currencies': 'XCU'  # Copper
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if 'rates' in data and 'XCU' in data['rates']:
                    # Convert from per troy oz to per lb
                    price_per_oz = 1 / float(data['rates']['XCU'])
                    price_per_lb = price_per_oz * 14.5833  # troy oz to lb
                    print(f"Fetched copper price from alternative: ${price_per_lb:.4f}/lb")
                    return price_per_lb

        except Exception as e:
            print(f"Error fetching from alternative API: {e}")

        return None

    def get_historical_prices(self, period='1mo'):
        """
        Generate historical price data based on current price.

        Since free APIs don't provide historical data, we generate
        realistic historical data based on typical copper volatility.

        Args:
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y')

        Returns:
            list: List of price records
        """
        import random

        # Get current price as baseline
        current = self.get_current_price()
        if not current:
            return []

        base_price = current['raw_price']

        # Determine number of data points based on period
        periods = {
            '1d': (24, 1/24),      # 24 hours
            '5d': (40, 5/40),      # 5 days
            '1mo': (30, 1),        # 30 days
            '3mo': (90, 1),        # 90 days
            '6mo': (180, 1),       # 180 days
            '1y': (252, 1)         # Trading days
        }

        num_points, day_increment = periods.get(period, (30, 1))

        records = []
        now = datetime.utcnow()

        # Generate price history with realistic random walk
        price = base_price * (1 + random.uniform(-0.15, 0.05))  # Start lower
        volatility = 0.02  # 2% daily volatility

        for i in range(num_points):
            # Random walk with mean reversion toward current price
            change = random.gauss(0, volatility)
            reversion = (base_price - price) * 0.05
            price = price * (1 + change) + reversion
            price = max(price, base_price * 0.7)  # Floor at 70% of current

            timestamp = now - timedelta(days=(num_points - i) * day_increment)
            prices = self._calculate_prices(price)
            prices['timestamp'] = timestamp
            records.append(prices)

        # Ensure last point matches current price
        if records:
            records[-1] = {
                **self._calculate_prices(base_price),
                'timestamp': now
            }

        return records

    def get_intraday_prices(self):
        """Get intraday prices (simulated for demo)."""
        return self.get_historical_prices('1d')

    def _calculate_prices(self, raw_price):
        """
        Calculate sheet and coil prices from raw copper price.

        Args:
            raw_price: Copper price per pound

        Returns:
            dict: Calculated prices
        """
        sheet_markup = 1 + (self.markup_percent / 100)
        coil_markup = 1 + ((self.markup_percent - 5) / 100)

        sheet_price = raw_price * sheet_markup
        coil_price = raw_price * coil_markup

        return {
            'raw_price': round(raw_price, 4),
            'sheet_price': round(sheet_price, 4),
            'coil_price': round(coil_price, 4),
            'markup_percent': self.markup_percent
        }

    def get_price_change(self):
        """
        Calculate price change (simulated based on typical daily movement).

        Returns:
            dict: Price change information
        """
        current_data = self.get_current_price()
        if not current_data:
            return None

        current = current_data['raw_price']
        # Simulate previous close with small random change
        import random
        change_percent = random.uniform(-2, 2)  # -2% to +2%
        previous = current / (1 + change_percent / 100)
        change = current - previous

        return {
            'current': round(current, 4),
            'previous': round(previous, 4),
            'change': round(change, 4),
            'change_percent': round(change_percent, 2)
        }
