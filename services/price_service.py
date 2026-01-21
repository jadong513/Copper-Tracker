"""Service for fetching and calculating copper prices."""

import os
import requests
from datetime import datetime, timedelta
from config import Config


class CopperPriceService:
    """Service for fetching copper prices from Metals-API."""

    METALS_API_URL = "https://metals-api.com/api/latest"

    def __init__(self):
        self.markup_percent = Config.FABRICATION_MARKUP_PERCENT
        self.api_key = os.getenv('METALS_API_KEY', '')
        self._last_known_price = None
        self._last_fetch_time = None
        self._is_live_data = False

    def get_current_price(self):
        """
        Fetch current copper price.

        Returns:
            dict: Current prices including raw, sheet, and coil
        """
        price = None

        # Try Metals-API if we have a key
        if self.api_key:
            price = self._fetch_from_metals_api()

        if price:
            self._last_known_price = price
            self._last_fetch_time = datetime.utcnow()
            self._is_live_data = True
            result = self._calculate_prices(price)
            result['is_live'] = True
            result['source'] = 'Metals-API'
            return result

        # Fallback to cached price
        if self._last_known_price:
            print("Using cached price data")
            result = self._calculate_prices(self._last_known_price)
            result['is_live'] = False
            result['source'] = 'Cached'
            return result

        # Demo mode
        print("Using demo price data - add METALS_API_KEY for live prices")
        demo_price = 4.45  # Realistic copper price per lb (Jan 2025)
        result = self._calculate_prices(demo_price)
        result['is_live'] = False
        result['source'] = 'Demo'
        return result

    def _fetch_from_metals_api(self):
        """Fetch copper price from Metals-API."""
        try:
            response = requests.get(
                self.METALS_API_URL,
                params={
                    'access_key': self.api_key,
                    'base': 'USD',
                    'symbols': 'XCU'  # Copper
                },
                timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data.get('success') and 'rates' in data:
                    # XCU rate is USD per troy oz, we need to convert
                    if 'XCU' in data['rates']:
                        # Rate is 1/price (how much copper per 1 USD)
                        rate = float(data['rates']['XCU'])
                        price_per_troy_oz = 1 / rate
                        # Convert troy oz to pounds (1 lb = 14.5833 troy oz)
                        price_per_lb = price_per_troy_oz / 14.5833
                        print(f"Fetched live copper price: ${price_per_lb:.4f}/lb")
                        return price_per_lb
                else:
                    error = data.get('error', {}).get('info', 'Unknown error')
                    print(f"Metals-API error: {error}")

        except Exception as e:
            print(f"Error fetching from Metals-API: {e}")

        return None

    def get_historical_prices(self, period='1mo'):
        """
        Get historical price data.

        Note: Free tier doesn't include historical data, so we generate
        realistic data based on current price and typical copper volatility.
        """
        import random
        random.seed(42)  # Consistent results

        current = self.get_current_price()
        if not current:
            return []

        base_price = current['raw_price']
        is_live = current.get('is_live', False)

        periods = {
            '1d': (24, 1/24),
            '5d': (40, 5/40),
            '1mo': (30, 1),
            '3mo': (90, 1),
            '6mo': (180, 1),
            '1y': (252, 1)
        }

        num_points, day_increment = periods.get(period, (30, 1))
        records = []
        now = datetime.utcnow()

        # Generate realistic price history
        price = base_price * 0.95  # Start slightly lower
        volatility = 0.015

        for i in range(num_points):
            change = random.gauss(0, volatility)
            reversion = (base_price - price) * 0.03
            price = price * (1 + change) + reversion
            price = max(price, base_price * 0.8)

            timestamp = now - timedelta(days=(num_points - i) * day_increment)
            prices = self._calculate_prices(price)
            prices['timestamp'] = timestamp
            prices['is_live'] = False  # Historical is always simulated on free tier
            records.append(prices)

        # Last point = current price
        if records:
            final = self._calculate_prices(base_price)
            final['timestamp'] = now
            final['is_live'] = is_live
            records[-1] = final

        return records

    def get_intraday_prices(self):
        """Get intraday prices."""
        return self.get_historical_prices('1d')

    def _calculate_prices(self, raw_price):
        """Calculate sheet and coil prices from raw copper price."""
        sheet_markup = 1 + (self.markup_percent / 100)
        coil_markup = 1 + ((self.markup_percent - 5) / 100)

        return {
            'raw_price': round(raw_price, 4),
            'sheet_price': round(raw_price * sheet_markup, 4),
            'coil_price': round(raw_price * coil_markup, 4),
            'markup_percent': self.markup_percent
        }

    def get_price_change(self):
        """Get price change info."""
        current_data = self.get_current_price()
        if not current_data:
            return None

        current = current_data['raw_price']

        # For accurate change, we'd need historical API access
        # Using small simulated change for demo
        import random
        change_percent = random.uniform(-1.5, 1.5)
        previous = current / (1 + change_percent / 100)

        return {
            'current': round(current, 4),
            'previous': round(previous, 4),
            'change': round(current - previous, 4),
            'change_percent': round(change_percent, 2),
            'is_live': current_data.get('is_live', False)
        }

    def is_using_live_data(self):
        """Check if currently using live data."""
        return self._is_live_data and self.api_key
