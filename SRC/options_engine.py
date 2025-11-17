# src/options_engine.py
import numpy as np
from scipy.stats import norm
import logging

logger = logging.getLogger(__name__)

class OptionsEngine:
    def __init__(self, multiplier=50):
        self.multiplier = multiplier
    
    def calculate_iron_butterfly(self, current_price, strike, premium_short, 
                                 premium_long_call, premium_long_put, width):
        """
        Iron Butterfly kolem magnetu
        """
        try:
            # Net premium
            net_premium = (premium_short * 2) - (premium_long_call + premium_long_put)
            
            # Max profit = net premium
            max_profit = net_premium * self.multiplier
            
            # Max risk = width - net premium
            max_risk = (width - net_premium) * self.multiplier
            
            # Break-even body
            upper_be = strike + net_premium
            lower_be = strike - net_premium
            
            return {
                "strategy": "Iron Butterfly",
                "strike": strike,
                "net_premium": net_premium,
                "max_profit": max_profit,
                "max_risk": max_risk,
                "upper_be": upper_be,
                "lower_be": lower_be,
                "risk_reward": max_profit / max_risk if max_risk > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating iron butterfly: {e}")
            return None
    
    def calculate_magnetic_strangle(self, magnet, price_call, price_put, 
                                   buy_call_strike, buy_put_strike):
        """
        "Strangle the Magnet" - vyšší RRR strategie
        """
        try:
            # Sell strangle těsně kolem magnetu
            sell_call_strike = magnet + 5  # +5 bodů
            sell_put_strike = magnet - 5   # -5 bodů
            
            # Net premium
            net_premium = price_call + price_put
            
            # Max risk = rozdíl mezi strike a ochrannými opcemi
            call_risk = abs(buy_call_strike - sell_call_strike)
            put_risk = abs(buy_put_strike - sell_put_strike)
            max_risk = max(call_risk, put_risk) * self.multiplier
            
            # Max profit
            max_profit = net_premium * self.multiplier
            
            return {
                "strategy": "Magnetic Strangle",
                "sell_call": sell_call_strike,
                "sell_put": sell_put_strike,
                "net_premium": net_premium,
                "max_profit": max_profit,
                "max_risk": max_risk,
                "risk_reward": max_profit / max_risk if max_risk > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Error calculating magnetic strangle: {e}")
            return None
    
    def estimate_probability(self, current_price, strike, days_to_expiry, 
                           volatility, option_type="call"):
        """
        Black-Scholes odhad pravděpodobnosti ITM
        """
        try:
            if volatility == 0 or current_price == 0:
                return 0.5
            
            # d1/d2
            time_to_expiry = days_to_expiry / 365.0
            d1 = (np.log(current_price / strike) + 
                  (0.5 * volatility**2 * time_to_expiry)) / \
                 (volatility * np.sqrt(time_to_expiry))
            d2 = d1 - volatility * np.sqrt(time_to_expiry)
            
            if option_type == "call":
                prob = norm.cdf(d2)
            else:
                prob = norm.cdf(-d2)
            
            return prob
            
        except Exception as e:
            logger.error(f"Error estimating probability: {e}")
            return 0.5
    
    def get_strategy_recommendation(self, magnet_data, volatility, 
                                   price_call=8.0, price_put=8.0):
        """
        Rozhodne kterou strategii použít na základě dat
        """
        try:
            magnet_level = magnet_data["level"]
            is_active = magnet_data["is_active"]
            time_at_level = magnet_data["time_at_level"]
            
            if not is_active:
                return {"action": "WAIT", "reason": "Magnet není aktivní"}
            
            if time_at_level > 0.7:
                # Silná konsolidace - Iron Butterfly
                strategy = self.calculate_iron_butterfly(
                    magnet_level, magnet_level, 25, 12.5, 12.5, 25
                )
                return {
                    "action": "SELL_IRON_BUTTERFLY",
                    "strategy": strategy,
                    "confidence": "HIGH"
                }
            elif time_at_level > 0.5:
                # Střední konsolidace - Strangle
                strategy = self.calculate_magnetic_strangle(
                    magnet_level, price_call, price_put, 
                    magnet_level+20, magnet_level-20
                )
                return {
                    "action": "SELL_STRANGLE",
                    "strategy": strategy,
                    "confidence": "MEDIUM"
                }
            else:
                return {"action": "WAIT", "reason": "Nedostatečná konsolidace"}
                
        except Exception as e:
            logger.error(f"Error getting recommendation: {e}")
            return {"action": "ERROR", "reason": str(e)}
