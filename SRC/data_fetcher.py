# src/data_fetcher.py
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ESDataFetcher:
    def __init__(self):
        self.es_symbol = "ES=F"
        self.vix_symbol = "^VIX"
    
    def get_current_data(self):
        """Získá aktuální cenu a základní data pro ES futures"""
        try:
            # ES futures
            es = yf.Ticker(self.es_symbol)
            es_data = es.history(period="1d", interval="1m")
            
            if es_data.empty:
                logger.error("Nemohu získat ES data")
                return None
            
            current_price = es_data['Close'].iloc[-1]
            current_volume = es_data['Volume'].iloc[-1]
            
            # VIX pro market sentiment
            vix = yf.Ticker(self.vix_symbol)
            vix_data = vix.history(period="1d", interval="1m")
            vix_level = vix_data['Close'].iloc[-1] if not vix_data.empty else 15
            
            return {
                "price": round(current_price, 2),
                "volume": int(current_volume),
                "vix": round(vix_level, 2),
                "timestamp": datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error fetching data: {e}")
            return None
    
    def get_historical_data(self, days=30):
        """Získá historická data pro backtesting"""
        try:
            es = yf.Ticker(self.es_symbol)
            hist = es.history(period=f"{days}d", interval="5m")
            
            if hist.empty:
                logger.error("Nemohu získat historická data")
                return None
            
            # Reset index pro práci s datetime
            hist = hist.reset_index()
            hist['Datetime'] = pd.to_datetime(hist['Datetime'])
            
            return hist
            
        except Exception as e:
            logger.error(f"Error fetching historical data: {e}")
            return None
    
    def get_volume_profile(self, data, price_levels):
        """Vytvoří volume profile pro dané cenové úrovně"""
        try:
            volume_profile = {}
            
            for level in price_levels:
                # Najdi obchody v toleranci ±3 body
                mask = (data['Close'] >= level - 3) & (data['Close'] <= level + 3)
                level_volume = data.loc[mask, 'Volume'].sum()
                volume_profile[level] = level_volume
            
            return volume_profile
            
        except Exception as e:
            logger.error(f"Error creating volume profile: {e}")
            return {}
