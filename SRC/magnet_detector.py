# src/magnet_detector.py
import numpy as np
import pandas as pd
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

class MagnetDetector:
    def __init__(self, multipliers=[50, 100], tolerance=3):
        self.multipliers = multipliers
        self.tolerance = tolerance
        self.magnet_memory = defaultdict(list)  # Ukládá historii magnetů
    
    def find_nearest_magnet(self, price):
        """Najde nejbližší psychologickou úroveň"""
        try:
            price_rounded = round(price)
            
            # Najdi nejbližší násobek 50 nebo 100
            magnets = []
            for mult in self.multipliers:
                base = (price_rounded // mult) * mult
                magnets.extend([base, base + mult])
            
            # Vyber nejbližší
            distances = [abs(price - m) for m in magnets]
            nearest_idx = np.argmin(distances)
            
            return magnets[nearest_idx], distances[nearest_idx]
            
        except Exception as e:
            logger.error(f"Error finding magnet: {e}")
            return None, None
    
    def detect_active_magnet(self, data, window=15):
        """
        Detekuje aktivní magnet na základě:
        1. Cena osciluje kolem úrovně
        2. Vysoký objem na této úrovni
        3. Čas strávený na úrovni
        """
        try:
            current_price = data['Close'].iloc[-1]
            magnet, distance = self.find_nearest_magnet(current_price)
            
            if distance > self.tolerance:
                logger.info(f"Cena {current_price} je příliš daleko od magnetu {magnet}")
                return None
            
            # Spočítej čas strávený na této úrovni
            recent_data = data.tail(window)
            in_range = 0
            
            for _, row in recent_data.iterrows():
                if abs(row['Close'] - magnet) <= self.tolerance:
                    in_range += 1
            
            time_at_level = in_range / window  # Procento času
            
            # Spočítej objem na této úrovni
            volume_profile = self.get_volume_at_level(recent_data, magnet)
            
            return {
                "level": magnet,
                "distance": distance,
                "time_at_level": time_at_level,
                "volume_at_level": volume_profile,
                "is_active": time_at_level > 0.6  # Aktivní pokud >60% času
            }
            
        except Exception as e:
            logger.error(f"Error detecting active magnet: {e}")
            return None
    
    def get_volume_at_level(self, data, magnet):
        """Spočítá objem na dané úrovni"""
        try:
            tolerance = self.tolerance
            mask = (data['Close'] >= magnet - tolerance) & \
                   (data['Close'] <= magnet + tolerance)
            
            return data.loc[mask, 'Volume'].sum()
            
        except Exception as e:
            logger.error(f"Error getting volume: {e}")
            return 0
    
    def calculate_market_memory_index(self, current_level, previous_magnet, atr_5d):
        """MMI = (Current - Previous) / ATR"""
        try:
            if not previous_magnet or atr_5d == 0:
                return 0
            
            mmi = (current_level - previous_magnet) / atr_5d
            return mmi
            
        except Exception as e:
            logger.error(f"Error calculating MMI: {e}")
            return 0
    
    def calculate_volume_liquidity_score(self, current_volume, avg_volume_20d, direction):
        """VLS = (Current_Volume / Avg_Volume) × Direction"""
        try:
            if avg_volume_20d == 0:
                return 0
            
            ratio = current_volume / avg_volume_20d
            vls = ratio * (1 if direction == "up" else -1)
            
            return vls
            
        except Exception as e:
            logger.error(f"Error calculating VLS: {e}")
            return 0
