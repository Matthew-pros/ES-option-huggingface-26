# src/backtester.py
import pandas as pd
import numpy as np
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Backtester:
    def __init__(self, data_fetcher, magnet_detector, options_engine, risk_manager):
        self.data_fetcher = data_fetcher
        self.magnet_detector = magnet_detector
        self.options_engine = options_engine
        self.risk_manager = risk_manager
        self.trades = []
    
    def run_backtest(self, days=30):
        """Spustí backtest na posledních N dnech"""
        try:
            logger.info(f"Spouštím backtest na {days} dní...")
            
            # Získej historická data
            data = self.data_fetcher.get_historical_data(days)
            if data is None:
                return None
            
            results = []
            daily_pnl = 0
            
            # Pro každý den
            for date, day_data in data.groupby(data['Datetime'].dt.date):
                logger.info(f"\n=== {date} ===")
                self.risk_manager.reset_daily_loss()
                
                # Pro každý 5m interval
                for i in range(20, len(day_data)):  # Začni po 20 ti minutách
                    window = day_data.iloc[i-20:i]
                    
                    # Detekuj aktivní magnet
                    magnet_data = self.magnet_detector.detect_active_magnet(window)
                    
                    if magnet_data and magnet_data['is_active']:
                        # Získej strategii
                        rec = self.options_engine.get_strategy_recommendation(
                            magnet_data, volatility=0.15
                        )
                        
                        if rec['action'].startswith("SELL"):
                            # Simuluj obchod
                            trade_result = self.simulate_trade(
                                rec, window.iloc[-1], magnet_data
                            )
                            results.append(trade_result)
                            
                            if trade_result['pnl'] < 0:
                                daily_pnl += trade_result['pnl']
                            else:
                                daily_pnl += trade_result['pnl']
                
                logger.info(f"Denní PNL: ${daily_pnl:,.2f}")
            
            return self.calculate_metrics(results)
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
            return None
    
    def simulate_trade(self, recommendation, current_data, magnet_data):
        """Simuluje jeden obchod"""
        try:
            strategy = recommendation['strategy']
            entry_price = current_data['Close']
            magnet = magnet_data['level']
            
            # Simulace výsledku
            # Pokud cena zůstane v pásmu ±8 bodů po 30 minutách = profit
            future_window = 6  # 30 minut = 6 × 5m
            
            # Zisková pravděpodobnost založená na time_at_level
            prob = magnet_data['time_at_level']
            
            # Náhodný výsledek založený na pravděpodobnosti
            is_winner = np.random.random() < prob
            
            if is_winner:
                pnl = strategy['max_profit']
                outcome = "WIN"
            else:
                pnl = -strategy['max_risk']
                outcome = "LOSS"
            
            trade = {
                "timestamp": datetime.now(),
                "magnet": magnet,
                "entry_price": entry_price,
                "strategy": strategy['strategy'],
                "pnl": pnl,
                "outcome": outcome,
                "risk_reward": strategy['risk_reward']
            }
            
            self.trades.append(trade)
            self.risk_manager.update_balance(pnl)
            
            return trade
            
        except Exception as e:
            logger.error(f"Error simulating trade: {e}")
            return None
    
    def calculate_metrics(self, trades):
        """Spočítá performance metriky"""
        if not trades:
            return None
        
        df = pd.DataFrame(trades)
        total_trades = len(df)
        winning_trades = len(df[df['outcome'] == 'WIN'])
        losing_trades = len(df[df['outcome'] == 'LOSS'])
        
        win_rate = winning_trades / total_trades
        avg_win = df[df['pnl'] > 0]['pnl'].mean()
        avg_loss = df[df['pnl'] < 0]['pnl'].mean()
        avg_pnl = df['pnl'].mean()
        
        total_pnl = df['pnl'].sum()
        
        # Profit Factor
        gross_profit = df[df['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(df[df['pnl'] < 0]['pnl'].sum())
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Edge
        edge = (win_rate * avg_win - (1-win_rate) * abs(avg_loss)) / abs(avg_loss)
        
        return {
            "total_trades": total_trades,
            "win_rate": win_rate,
            "avg_win": avg_win,
            "avg_loss": avg_loss,
            "avg_pnl": avg_pnl,
            "total_pnl": total_pnl,
            "profit_factor": profit_factor,
            "edge": edge,
            "final_balance": self.risk_manager.current_balance
        }
