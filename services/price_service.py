"""Service for fetching and calculating copper prices."""

import yfinance as yf
from datetime import datetime, timedelta
from config import Config


class CopperPriceService:
    """Service for fetching copper prices from Yahoo Finance."""

    def __init__(self):
        self.symbol = Config.COPPER_SYMBOL
        self.markup_percent = Config.FABRICATION_MARKUP_PERCENT
        self._last_known_price = None

    def get_current_price(self):
        """
        Fetch current COMEX copper futures price.

        Returns:
            dict: Current prices including raw, sheet, and coil
        """
        try:
            ticker = yf.Ticker(self.symbol)
            # Try 5d period for more reliable data
            data = ticker.history(period='5d')

            if data.empty:
                print(f"No data returned for {self.symbol}, trying fallback...")
                # Try alternative approach
                info = ticker.info
                if info and 'regularMarketPrice' in info:
                    raw_price = float(info['regularMarketPrice'])
                    self._last_known_price = raw_price
                    return self._calculate_prices(raw_price)
                # Return last known price if available
                if self._last_known_price:
                    return self._calculate_prices(self._last_known_price)
                return None

            raw_price = float(data['Close'].iloc[-1])
            self._last_known_price = raw_price

            return self._calculate_prices(raw_price)

        except Exception as e:
            print(f"Error fetching copper price: {e}")
            # Return last known price on error
            if self._last_known_price:
                return self._calculate_prices(self._last_known_price)
            return None

    def get_historical_prices(self, period='1mo'):
        """
        Fetch historical copper prices.

        Args:
            period: Time period ('1d', '5d', '1mo', '3mo', '6mo', '1y', '2y', '5y')

        Returns:
            list: List of price records
        """
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period=period)

            if data.empty:
                return []

            records = []
            for timestamp, row in data.iterrows():
                raw_price = float(row['Close'])
                prices = self._calculate_prices(raw_price)
                prices['timestamp'] = timestamp.to_pydatetime()
                records.append(prices)

            return records

        except Exception as e:
            print(f"Error fetching historical prices: {e}")
            return []

    def get_intraday_prices(self):
        """
        Fetch intraday copper prices (5-minute intervals).

        Returns:
            list: List of intraday price records
        """
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period='1d', interval='5m')

            if data.empty:
                return []

            records = []
            for timestamp, row in data.iterrows():
                raw_price = float(row['Close'])
                prices = self._calculate_prices(raw_price)
                prices['timestamp'] = timestamp.to_pydatetime()
                records.append(prices)

            return records

        except Exception as e:
            print(f"Error fetching intraday prices: {e}")
            return []

    def _calculate_prices(self, raw_price):
        """
        Calculate sheet and coil prices from raw copper price.

        Args:
            raw_price: COMEX copper price per pound

        Returns:
            dict: Calculated prices
        """
        # 16oz = 1 pound, so raw price is per 16oz
        # Sheet has higher fabrication cost than coil
        sheet_markup = 1 + (self.markup_percent / 100)
        coil_markup = 1 + ((self.markup_percent - 5) / 100)  # Coil typically 5% less markup

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
        Calculate price change from previous close.

        Returns:
            dict: Price change information
        """
        try:
            ticker = yf.Ticker(self.symbol)
            data = ticker.history(period='2d')

            if len(data) < 2:
                return None

            current = float(data['Close'].iloc[-1])
            previous = float(data['Close'].iloc[-2])
            change = current - previous
            change_percent = (change / previous) * 100

            return {
                'current': round(current, 4),
                'previous': round(previous, 4),
                'change': round(change, 4),
                'change_percent': round(change_percent, 2)
            }

        except Exception as e:
            print(f"Error calculating price change: {e}")
            return None
