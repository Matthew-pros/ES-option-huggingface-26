# main.py
import streamlit as st
import sys
sys.path.append('.')
from config import *
from src.data_fetcher import ESDataFetcher
from src.magnet_detector import MagnetDetector
from src.options_engine import OptionsEngine
from src.risk_manager import RiskManager
from src.backtester import Backtester
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)

# Page config
st.set_page_config(
    page_title="ES Magnet Trading System",
    page_icon="📊",
    layout="wide"
)

# Title
st.title("🎯 ES Magnet Trading System")
st.markdown("***Obchodování jako Kasino - Bez Grafů, Pouze Matematika***")

# Sidebar - Nastavení účtu
st.sidebar.header("Nastavení Účtu")
account_balance = st.sidebar.number_input(
    "Počáteční Kapitál ($)", 
    min_value=10000, 
    max_value=1000000, 
    value=100000,
    step=5000
)

max_daily_loss_pct = st.sidebar.slider(
    "Max Denní Ztráta (%)", 
    min_value=1.0, 
    max_value=5.0, 
    value=3.0,
    step=0.5
)

# Inicializace komponentů
@st.cache_resource
def init_system(balance, daily_loss_pct):
    data_fetcher = ESDataFetcher()
    magnet_detector = MagnetDetector(
        multipliers=[50, 100],
        tolerance=MAGNET_TOLERANCE
    )
    options_engine = OptionsEngine(
        multiplier=ES_OPTION_MULTIPLIER
    )
    risk_manager = RiskManager(
        account_balance=balance,
        max_daily_loss=daily_loss_pct/100,
        max_trade_loss=0.01,
        kelly_fraction=KELLY_FRACTION
    )
    backtester = Backtester(
        data_fetcher, magnet_detector, options_engine, risk_manager
    )
    return data_fetcher, magnet_detector, options_engine, risk_manager, backtester

data_fetcher, magnet_detector, options_engine, risk_manager, backtester = init_system(
    account_balance, max_daily_loss_pct
)

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["LIVE TRADING", "BACKTEST", "RISK METRICS", "JAK TO FUNGUJE"])

# Tab 1: Live Trading
with tab1:
    st.header("Živé Obchodní Signály")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("ZÍSKAT AKTUÁLNÍ DATA", type="primary"):
            data = data_fetcher.get_current_data()
            
            if data:
                st.metric("ES Futures", f"${data['price']:,.2f}")
                st.metric("VIX", f"{data['vix']:.2f}")
                st.metric("Volume", f"{data['volume']:,}")
            else:
                st.error("Nemohu získat data")
    
    with col2:
        if st.button("ANALYZUJ MAGNET"):
            data = data_fetcher.get_current_data()
            if data:
                # Získej poslední data (simulace 5m okna)
                hist = data_fetcher.get_historical_data(days=1)
                if hist is not None and len(hist) > 20:
                    window = hist.tail(20)
                    magnet_data = magnet_detector.detect_active_magnet(window)
                    
                    if magnet_data:
                        st.success(f"AKTIVNÍ MAGNET: {magnet_data['level']}")
                        st.info(f"Vzdálenost: {magnet_data['distance']} bodů")
                        st.info(f"Čas na úrovni: {magnet_data['time_at_level']:.1%}")
                    else:
                        st.warning("Žádný aktivní magnet")
                else:
                    st.error("Nedostatek dat")
    
    with col3:
        if st.button("GENERUJ SIGNÁL"):
            data = data_fetcher.get_current_data()
            if data:
                hist = data_fetcher.get_historical_data(days=1)
                if hist is not None and len(hist) > 20:
                    window = hist.tail(20)
                    magnet_data = magnet_detector.detect_active_magnet(window)
                    
                    if magnet_data and magnet_data['is_active']:
                        rec = options_engine.get_strategy_recommendation(
                            magnet_data
                        )
                        
                        st.subheader("🎯 OBCHODNÍ SIGNÁL")
                        st.json(rec)
                        
                        # Zobraz Kelly sizing
                        if rec['action'].startswith("SELL"):
                            size = risk_manager.get_position_size(rec['strategy'])
                            st.metric("Velikost pozice", f"{size} kontraktů")
                    else:
                        st.info("ČEKEJ - žádný aktivní setup")

# Tab 2: Backtest
with tab2:
    st.header("Backtesting Engine")
    
    days = st.slider("Dny pro backtest", 7, 365, 30)
    
    if st.button("SPOUSTÍM BACKTEST", type="primary"):
        with st.spinner("Backtesting..."):
            results = backtester.run_backtest(days=days)
            
            if results:
                st.success("Backtest dokončen!")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Celkové obchody", results['total_trades'])
                    st.metric("Win Rate", f"{results['win_rate']:.1%}")
                    st.metric("Profit Factor", f"{results['profit_factor']:.2f}")
                
                with col2:
                    st.metric("Avg Win", f"${results['avg_win']:,.2f}")
                    st.metric("Avg Loss", f"${results['avg_loss']:,.2f}")
                    st.metric("Edge", f"{results['edge']:.1%}")
                
                with col3:
                    st.metric("Celkový PnL", f"${results['total_pnl']:,.2f}")
                    st.metric("Finální Balance", f"${results['final_balance']:,.2f}")
                    
                    if results['edge'] > 0.15:
                        st.success("✅ EDGE JE KASINO-LEVEL")
                    elif results['edge'] > 0:
                        st.warning("⚠️ MÍRNÁ EDGE")
                    else:
                        st.error("❌ NEGATIVNÍ EDGE")
            else:
                st.error("Backtest selhal")

# Tab 3: Risk Metrics
with tab3:
    st.header("Risk Management Dashboard")
    
    metrics = risk_manager.get_risk_metrics()
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Aktuální Balance", f"${metrics['current_balance']:,.2f}")
        st.metric("Denní Ztráta", f"${metrics['daily_loss']:,.2f}")
        st.metric("Limit Denní Ztráty", f"${metrics['daily_loss_limit']:,.2f}")
    
    with col2:
        st.metric("Zůstávající Riziko", f"${metrics['remaining_daily_risk']:,.2f}")
        
        if metrics['can_trade']:
            st.success("✅ Můžeš obchodovat")
        else:
            st.error("⛔ DAILY LIMIT - STOP TRADING")

# Tab 4: Jak to funguje
with tab4:
    st.header("📖 Principy Systému")
    
    st.markdown("""
    ### **1. Psychologické Magnety**
    Trh se chová jako živý organismus. Pracuje s celými čísly (6650, 6700, 6750) protože:
    - Lidé myslí v celých číslech
    - Algoritmy shromažďují příkazy kolem těchto úrovní
    - Vzniká tam největší likvidita
    
    ### **2. Matematický Edge**
    Systém detekuje kdy se cena "zasekne" kolem magnetu:
    - >60% času v pásmu ±3 body
    - Vysoký objem
    - VIX < 15 (low volatility regime)
    
    Poté prodáváme opční prémie = Kasino edge
    
    ### **3. Opční Strategie**
    - **Iron Butterfly**: Nejvyšší pravděpodobnost úspěchu (70%+)
    - **Magnetic Strangle**: Vyšší RRR (3:1+)
    
    ### **4. Kelly Sizing**
    `Fraction = (W×(R+1) - 1) / R`
    - Používáme 1/4 Kelly pro konzervaci
    - Omezeno na 1% risk na obchod
    
    ### **5. Risk Management**
    - Max 3% denní ztráta = HARD STOP
    - Každý obchod má definovaný risk předem
    - Matematika > Emoce
    """)

st.sidebar.info("Systém používá yfinance pro data. Pro live trading zvažte profesionální API.")
