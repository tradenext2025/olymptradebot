import json
import threading
import time
import ssl
import websocket
import urllib.request
from config import OLYMP_TOKEN, BASE_PRICES

live_prices    = {}
candle_history = {}
ws_connected   = False

SYMBOL_MAP = {
    "Bitcoin OTC":     "BTCUSD_OTC",
    "Ripple OTC":      "XRPUSD_OTC",
    "Dogecoin OTC":    "DOGEUSD_OTC",
    "Ethereum OTC":    "ETHUSD_OTC",
    "Litecoin OTC":    "LTCUSD_OTC",
    "EUR/USD OTC":     "EURUSD_OTC",
    "GBP/USD OTC":     "GBPUSD_OTC",
    "USD/JPY OTC":     "USDJPY_OTC",
    "AUD/USD OTC":     "AUDUSD_OTC",
    "USD/CAD OTC":     "USDCAD_OTC",
    "USD/CHF OTC":     "USDCHF_OTC",
    "NZD/USD OTC":     "NZDUSD_OTC",
    "EUR/GBP OTC":     "EURGBP_OTC",
    "EUR/JPY OTC":     "EURJPY_OTC",
    "GBP/JPY OTC":     "GBPJPY_OTC",
    "GBP/AUD OTC":     "GBPAUD_OTC",
    "GBP/CAD OTC":     "GBPCAD_OTC",
    "GBP/CHF OTC":     "GBPCHF_OTC",
    "GBP/NZD OTC":     "GBPNZD_OTC",
    "Gold OTC":        "XAUUSD_OTC",
    "Silver OTC":      "XAGUSD_OTC",
    "Oil OTC":         "USOIL_OTC",
    "Compound Index":  "COMPOUND_INDEX",
    "AUS 200 OTC":     "AUS200_OTC",
    "US 500 OTC":      "US500_OTC",
    "US TECH 100 OTC": "USTECH100_OTC",
}
REVERSE_MAP = {v: k for k, v in SYMBOL_MAP.items()}

def get_live_price(asset):
    return live_prices.get(asset)

def get_ws_status():
    return ws_connected

def get_candle_history(asset, n=60):
    return candle_history.get(asset, [])[-n:]

def on_open(ws):
    global ws_connected
    ws_connected = True
    print("WebSocket connected to OlympTrade!")

    # Step 1: Authenticate with token
    ws.send(json.dumps({
        "action": "setToken",
        "message": {
            "token": OLYMP_TOKEN
        }
    }))
    time.sleep(1)

    # Step 2: Subscribe to candles for each asset
    for asset_name, symbol in SYMBOL_MAP.items():
        try:
            # Subscribe to 5s candles
            ws.send(json.dumps({
                "action": "subscribeCandle",
                "message": {
                    "instrument": symbol,
                    "duration":   5
                }
            }))
            time.sleep(0.1)
        except Exception as e:
            print(f"Subscribe error {symbol}: {e}")

    print("Subscribed to all OTC assets!")

def on_message(ws, message):
    global live_prices, candle_history
    try:
        data = json.loads(message)

        # Handle different message formats
        action = data.get("action", "")
        msg    = data.get("message", {})

        # Format 1: candle update
        if action == "candle" or action == "candle-created":
            symbol = msg.get("instrument", "")
            asset  = REVERSE_MAP.get(symbol, "")
            if asset and msg.get("close"):
                price = float(msg["close"])
                live_prices[asset] = price
                _add_candle(asset, msg)

        # Format 2: tick/quote
        elif action in ["tick", "quote", "price-changed"]:
            symbol = msg.get("instrument", "") or msg.get("symbol", "")
            asset  = REVERSE_MAP.get(symbol, "")
            price  = msg.get("close") or msg.get("price") or msg.get("ask")
            if asset and price:
                live_prices[asset] = float(price)

        # Format 3: nested data array
        elif "data" in data:
            items = data["data"]
            if isinstance(items, list):
                for item in items:
                    symbol = item.get("instrument", "")
                    asset  = REVERSE_MAP.get(symbol, "")
                    price  = item.get("close") or item.get("price")
                    if asset and price:
                        live_prices[asset] = float(price)
                        _add_candle(asset, item)

        # Format 4: direct price message
        elif "instrument" in msg and "close" in msg:
            symbol = msg["instrument"]
            asset  = REVERSE_MAP.get(symbol, "")
            if asset:
                live_prices[asset] = float(msg["close"])
                _add_candle(asset, msg)

    except Exception as e:
        pass

def _add_candle(asset, msg):
    global candle_history
    try:
        close = float(msg.get("close", 0))
        if close <= 0:
            return
        candle = {
            "open":   float(msg.get("open",   close)),
            "close":  close,
            "high":   float(msg.get("high",   close)),
            "low":    float(msg.get("low",    close)),
            "volume": int(msg.get("volume",   0)),
        }
        if asset not in candle_history:
            candle_history[asset] = []
        candle_history[asset].append(candle)
        if len(candle_history[asset]) > 200:
            candle_history[asset] = candle_history[asset][-200:]
    except:
        pass

def on_error(ws, error):
    global ws_connected
    ws_connected = False
    print(f"WebSocket error: {error}")

def on_close(ws, code, msg):
    global ws_connected
    ws_connected = False
    print(f"WebSocket closed: {code}")

def start_websocket():
    def run():
        while True:
            try:
                print("Connecting to OlympTrade WebSocket...")
                ws = websocket.WebSocketApp(
                    "wss://ws.olymptrade.com/",
                    header={
                        "Cookie":        f"access_token={OLYMP_TOKEN}",
                        "Authorization": f"Bearer {OLYMP_TOKEN}",
                        "Origin":        "https://olymptrade.com",
                    },
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close,
                )
                ws.run_forever(
                    sslopt={"cert_reqs": ssl.CERT_NONE},
                    ping_interval=20,
                    ping_timeout=10
                )
            except Exception as e:
                print(f"WebSocket crashed: {e}")
            print("Reconnecting in 5 seconds...")
            time.sleep(5)

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("WebSocket thread started!")
