"""Configuration settings for Copper Price Tracker."""

import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Application configuration."""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///copper_prices.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Price fetching
    COPPER_SYMBOL = 'HG=F'  # COMEX Copper Futures
    PRICE_UPDATE_INTERVAL_MINUTES = int(os.getenv('UPDATE_INTERVAL', '15'))

    # 16oz copper sheet calculation
    # Raw copper is priced per pound on COMEX
    # 16oz (1 lb) sheet typically has fabrication markup
    FABRICATION_MARKUP_PERCENT = float(os.getenv('FABRICATION_MARKUP', '35'))

    # Alerts
    ALERT_CHECK_INTERVAL_MINUTES = 5
