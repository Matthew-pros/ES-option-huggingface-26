# src/risk_manager.py
import numpy as np
import logging

logger = logging.getLogger(__name__)

class RiskManager:
    def __init__(self, account_balance, max_daily_loss=0.03, 
                 max_trade_loss=0.01, kelly_fraction=0.25):
        self.initial_balance = account_balance
        self.current_balance = account_balance
        self.max_daily_loss = max_daily_loss
        self.max_trade_loss = max_trade_loss
        self.kelly_fraction = kelly_fraction
        self.daily_loss = 0
        logger.info(f"RiskManager inicializován: ${account_balance:,.2f}")
    
    def reset_daily_loss(self):
        """Resetuje denní ztrátu"""
        self.daily_loss = 0
        logger.info("Denní ztráta resetována")
    
    def can_trade(self):
        """Kontrola zda můžeme obchodovat"""
        if self.daily_loss >= (self.max_daily_loss * self.initial_balance):
            logger.warning(f"DAILY LIMIT REACHED! Ztráta: ${self.daily_loss:,.2f}")
            return False
        return True
    
    def calculate_kelly_position(self, win_prob, win_loss_ratio):
        """
        Kelly Criterium: Fraction = (W×(R+1) - 1) / R
        """
        try:
            if win_loss_ratio <= 0:
                return 0
            
            # Kelly formula
            kelly = (win_prob * (win_loss_ratio + 1) - 1) / win_loss_ratio
            
            # Konzervativní frakce
            position = kelly * self.kelly_fraction
            
            # Omezení na max trade loss
            max_risk_amount = self.max_trade_loss * self.current_balance
            position = min(position, max_risk_amount)
            
            logger.info(f"Kelly pozice: {position:.4f} ({kelly:.4f} full Kelly)")
            return max(0, position)
            
        except Exception as e:
            logger.error(f"Error in Kelly calculation: {e}")
            return 0
    
    def update_balance(self, pnl):
        """Aktualizuje balance po obchodu"""
        self.current_balance += pnl
        self.daily_loss += max(0, -pnl)
        logger.info(f"PNL: ${pnl:,.2f}, Nový balance: ${self.current_balance:,.2f}")
    
    def get_position_size(self, strategy, win_prob=0.68):
        """Spočítá velikost pozice pro strategii"""
        try:
            if not strategy or 'risk_reward' not in strategy:
                return 0
            
            risk_reward = strategy['risk_reward']
            max_risk = strategy['max_risk']
            
            # Kelly sizing
            position = self.calculate_kelly_position(win_prob, risk_reward)
            
            # Velikost v kontraktech
            contracts = position / max_risk if max_risk > 0 else 0
            
            logger.info(f"Velikost pozice: {contracts:.2f} kontraktů")
            return int(np.floor(contracts))
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0
    
    def get_risk_metrics(self):
        """Vrátí aktuální risk metriky"""
        return {
            "current_balance": self.current_balance,
            "daily_loss": self.daily_loss,
            "daily_loss_limit": self.max_daily_loss * self.initial_balance,
            "remaining_daily_risk": (self.max_daily_loss * self.initial_balance) - self.daily_loss,
            "can_trade": self.can_trade()
        }
