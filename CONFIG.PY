# config.py
import os
from pathlib import Path

# Cesty
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# ES Futures symbol
ES_SYMBOL = "ES=F"
VIX_SYMBOL = "^VIX"

# Psychologické úrovně
MAGNET_MULTIPLIERS = [50, 100]
MAGNET_TOLERANCE = 3  # body od úrovně

# Riziko
MAX_DAILY_LOSS = 0.03  # 3%
MAX_TRADE_LOSS = 0.01  # 1%
KELLY_FRACTION = 0.25  # Používáme 1/4 Kelly

# Opce (ES options - přibližné, v reálu použijte options API)
ES_OPTION_MULTIPLIER = 50  # $50 za bod
OPTION_PREMIUM_TARGET = 10  # bodů
OPTION_SPREAD_WIDTH = 15   # body ochrany

# Časování
SESSION_START = "09:30"
SESSION_END = "16:00"
MAGNET_HOLD_TIME = 15  # minut

# Vstupní podmínky
VP_RATIO_THRESHOLD = 1.3
MMI_THRESHOLD = 1.5
VLS_THRESHOLD = 2.0

# API klíče (pro reálná data)
POLYGON_API_KEY = os.getenv("POLYGON_API_KEY", "")
