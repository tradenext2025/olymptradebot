# ─── OLYMPTRADE WEBSOCKET CLIENT ──────────────────────────────────────────────
import json
import threading
import time
import ssl
import websocket
from config import OLYMP_TOKEN

# ── LIVE PRICE STORE ──────────────────────────────────────────────────────────
live_prices = {}   # { "EURUSD": 1.08542 }
ws_connected = False
ws_app = None

# Asset symbol map (OlympTrade internal symbols)
SYMBOL_MAP = {
    "Bitcoin OTC":      "BTCUSD_OTC",
    "Ripple OTC":       "XRPUSD_OTC",
    "Dogecoin OTC":     "DOGEUSD_OTC",
    "Ethereum OTC":     "ETHUSD_OTC",
    "Litecoin OTC":     "LTCUSD_OTC",
    "EUR/USD OTC":      "EURUSD_OTC",
    "GBP/USD OTC":      "GBPUSD_OTC",
    "USD/JPY OTC":      "USDJPY_OTC",
    "AUD/USD OTC":      "AUDUSD_OTC",
    "USD/CAD OTC":      "USDCAD_OTC",
    "USD/CHF OTC":      "USDCHF_OTC",
    "NZD/USD OTC":      "NZDUSD_OTC",
    "EUR/GBP OTC":      "EURGBP_OTC",
    "EUR/JPY OTC":      "EURJPY_OTC",
    "GBP/JPY OTC":      "GBPJPY_OTC",
    "GBP/AUD OTC":      "GBPAUD_OTC",
    "GBP/CAD OTC":      "GBPCAD_OTC",
    "GBP/CHF OTC":      "GBPCHF_OTC",
    "GBP/NZD OTC":      "GBPNZD_OTC",
    "Gold OTC":         "XAUUSD_OTC",
    "Silver OTC":       "XAGUSD_OTC",
    "Oil OTC":          "USOIL_OTC",
    "Compound Index":   "COMPOUND_INDEX",
    "AUS 200 OTC":      "AUS200_OTC",
    "US 500 OTC":       "US500_OTC",
    "US TECH 100 OTC":  "USTECH100_OTC",
}

REVERSE_MAP = {v: k for k, v in SYMBOL_MAP.items()}

# Candle history store per asset
candle_history = {}  # { "Bitcoin OTC": [candles...] }

def get_live_price(asset):
    return live_prices.get(asset)

def get_ws_status():
    return ws_connected

# ── WEBSOCKET HANDLERS ────────────────────────────────────────────────────────
def on_open(ws):
    global ws_connected
    ws_connected = True
    print("WebSocket connected to OlympTrade")

    # Authenticate
    auth_msg = json.dumps({
        "action": "setToken",
        "message": {"token": OLYMP_TOKEN}
    })
    ws.send(auth_msg)

    # Subscribe to all assets
    for asset, symbol in SYMBOL_MAP.items():
        sub_msg = json.dumps({
            "action": "subscribe",
            "message": {
                "name": "candle",
                "params": {
                    "instrument": symbol,
                    "duration": 5   # 5 second candles
                }
            }
        })
        ws.send(sub_msg)
        time.sleep(0.05)

    print("Subscribed to all OTC assets")

def on_message(ws, message):
    global live_prices, candle_history
    try:
        data = json.loads(message)
        action = data.get("action", "")

        # Price tick
        if action in ["candle", "tick", "quote"]:
            msg = data.get("message", {})
            symbol = msg.get("instrument") or msg.get("symbol", "")
            close  = msg.get("close") or msg.get("price") or msg.get("ask")

            if symbol and close:
                asset = REVERSE_MAP.get(symbol, symbol)
                live_prices[asset] = float(close)

                # Build candle history
                if asset not in candle_history:
                    candle_history[asset] = []

                candle = {
                    "open":   float(msg.get("open", close)),
                    "close":  float(close),
                    "high":   float(msg.get("high", close)),
                    "low":    float(msg.get("low", close)),
                    "volume": int(msg.get("volume", 0)),
                }
                candle_history[asset].append(candle)

                # Keep last 100 candles
                if len(candle_history[asset]) > 100:
                    candle_history[asset] = candle_history[asset][-100:]

    except Exception as e:
        pass

def on_error(ws, error):
    global ws_connected
    ws_connected = False
    print(f"WebSocket error: {error}")

def on_close(ws, code, msg):
    global ws_connected
    ws_connected = False
    print(f"WebSocket closed: {code}")

# ── START WEBSOCKET ────────────────────────────────────────────────────────────
def start_websocket():
    global ws_app

    def run():
        global ws_app
        while True:
            try:
                ws_app = websocket.WebSocketApp(
                    "wss://ws.olymptrade.com/",
                    header={"Authorization": f"Bearer {OLYMP_TOKEN}"},
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                )
                ws_app.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_NONE},
                    ping_interval=30,
                    ping_timeout=10
                )
            except Exception as e:
                print(f"WebSocket crashed: {e}")
            print("Reconnecting WebSocket in 5 seconds...")
            time.sleep(5)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("WebSocket thread started")

def get_candle_history(asset, n=60):
    return candle_history.get(asset, [])[-n:]
