import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8972480830:AAEF4XB9MWJzYWPqcrLqz6TNybQRhW3pny8")
ADMIN_ID       = int(os.environ.get("ADMIN_ID", "7664139802"))
OLYMP_TOKEN    = os.environ.get("OLYMP_TOKEN", "")
OLYMP_WS_URL   = "wss://ws.olymptrade.com"

# Auto login credentials
ADMIN_EMAIL    = os.environ.get("alisterc944@gmail.com",    "")
ADMIN_PASSWORD = os.environ.get("@Alister02#", "")

BOT_NAME       = "Nexus OlympTrade Bot"
VERSION        = "2.0.0"
ANALYSIS_TIME  = 12
TIMEFRAMES     = {"5s": 5, "10s": 10, "30s": 30, "1m": 60, "5m": 300}
DURATIONS      = ["5 sec","10 sec","15 sec","30 sec","1 min","2 min","3 min","5 min"]
AUTO_SIGNAL_INTERVAL = 120
BB_PERIOD      = 20
BB_STD         = 2
STOCH_K_PERIOD = 14
STOCH_D_PERIOD = 3
STOCH_SMOOTH   = 3
STOCH_OVERBOUGHT = 80
STOCH_OVERSOLD   = 20

ASSETS = {
    "crypto_otc":    {"label": "Crypto OTC",    "emoji": "₿",  "pairs": ["Bitcoin OTC","Ripple OTC","Dogecoin OTC","Ethereum OTC","Litecoin OTC"]},
    "forex_otc":     {"label": "Forex OTC",     "emoji": "💶", "pairs": ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","USD/CHF OTC","NZD/USD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","GBP/AUD OTC","GBP/CAD OTC","GBP/CHF OTC","GBP/NZD OTC"]},
    "commodity_otc": {"label": "Commodity OTC", "emoji": "🥇", "pairs": ["Gold OTC","Silver OTC","Oil OTC"]},
    "index_otc":     {"label": "Index OTC",     "emoji": "📊", "pairs": ["Compound Index","AUS 200 OTC","US 500 OTC","US TECH 100 OTC"]},
}
ALL_PAIRS = [p for cat in ASSETS.values() for p in cat["pairs"]]

BASE_PRICES = {
    "Bitcoin OTC": 62450.50, "Ripple OTC": 0.52340,
    "Dogecoin OTC": 0.15820, "Ethereum OTC": 3210.75,
    "Litecoin OTC": 85.320,
    "EUR/USD OTC": 1.08542, "GBP/USD OTC": 1.27341,
    "USD/JPY OTC": 149.823, "AUD/USD OTC": 0.65120,
    "USD/CAD OTC": 1.36540, "USD/CHF OTC": 0.89230,
    "NZD/USD OTC": 0.60120, "EUR/GBP OTC": 0.85320,
    "EUR/JPY OTC": 162.540, "GBP/JPY OTC": 190.230,
    "GBP/AUD OTC": 1.95420, "GBP/CAD OTC": 1.73210,
    "GBP/CHF OTC": 1.13540, "GBP/NZD OTC": 2.11230,
    "Gold OTC": 2345.60, "Silver OTC": 27.850,
    "Oil OTC": 78.320, "Compound Index": 7657.15,
    "AUS 200 OTC": 7842.50, "US 500 OTC": 5123.40,
    "US TECH 100 OTC": 18234.60,
}

LANGUAGES    = {"en":"English","sw":"Swahili","fr":"French","ar":"Arabic","pt":"Portuguese","es":"Spanish"}
DEFAULT_LANG = "en"
