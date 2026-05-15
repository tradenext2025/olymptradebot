# ─── REAL OLYMPTRADE PRICE FEED (Selenium on Railway) ─────────────────────────
import threading
import time
import json
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

def get_smart_price(asset):
    real = live_prices.get(asset)
    if real:
        return real, True
    return BASE_PRICES.get(asset, 1.0), False

def _add_candle(asset, open_, close, high, low, volume=0):
    if asset not in candle_history:
        candle_history[asset] = []
    candle_history[asset].append({
        "open": float(open_), "close": float(close),
        "high": float(high),  "low":   float(low),
        "volume": int(volume),
    })
    if len(candle_history[asset]) > 300:
        candle_history[asset] = candle_history[asset][-300:]

# ── SELENIUM PRICE FETCHER ────────────────────────────────────────────────────
def _selenium_loop():
    global ws_connected, live_prices
    while True:
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.chrome.service import Service
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC

            print("Starting Selenium Chrome...")
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_experimental_option("excludeSwitches", ["enable-automation"])

            driver = webdriver.Chrome(options=options)

            # Login to OlympTrade
            print("Opening OlympTrade...")
            driver.get("https://olymptrade.com/platform")
            time.sleep(3)

            # Inject access token as cookie
            driver.add_cookie({
                "name":   "access_token",
                "value":  OLYMP_TOKEN,
                "domain": ".olymptrade.com",
                "path":   "/",
            })
            driver.refresh()
            time.sleep(5)

            print("Logged into OlympTrade via Selenium!")
            ws_connected = True

            # Inject WebSocket interceptor
            ws_script = """
            window._prices = {};
            window._candles = {};

            const OrigWS = window.WebSocket;
            function PatchedWS(url, protocols) {
                const ws = protocols ? new OrigWS(url, protocols) : new OrigWS(url);
                ws.addEventListener('message', function(event) {
                    try {
                        const data = JSON.parse(event.data);
                        const action = data.action || '';
                        const msg = data.message || {};

                        if (action === 'candle' || action === 'candle-created') {
                            const sym = msg.instrument || '';
                            const close = msg.close;
                            if (sym && close) {
                                window._prices[sym] = parseFloat(close);
                                if (!window._candles[sym]) window._candles[sym] = [];
                                window._candles[sym].push({
                                    open: parseFloat(msg.open || close),
                                    close: parseFloat(close),
                                    high: parseFloat(msg.high || close),
                                    low: parseFloat(msg.low || close),
                                    volume: parseInt(msg.volume || 0)
                                });
                                if (window._candles[sym].length > 200)
                                    window._candles[sym] = window._candles[sym].slice(-200);
                            }
                        }

                        if (action === 'tick' || action === 'quote') {
                            const sym = msg.instrument || msg.symbol || '';
                            const price = msg.close || msg.price || msg.ask;
                            if (sym && price) {
                                window._prices[sym] = parseFloat(price);
                            }
                        }

                        // Handle array data
                        if (data.d && Array.isArray(data.d)) {
                            data.d.forEach(function(item) {
                                const sym = item.p || item.instrument || '';
                                const price = item.q || item.close || item.price;
                                if (sym && price) window._prices[sym] = parseFloat(price);
                            });
                        }
                    } catch(e) {}
                });
                return ws;
            }
            PatchedWS.prototype = OrigWS.prototype;
            window.WebSocket = PatchedWS;
            console.log('WebSocket interceptor injected!');
            """
            driver.execute_script(ws_script)
            print("WebSocket interceptor injected!")
            time.sleep(5)

            # Poll prices every 2 seconds
            while True:
                try:
                    prices_js = driver.execute_script("return JSON.stringify(window._prices || {})")
                    candles_js = driver.execute_script("return JSON.stringify(window._candles || {})")

                    if prices_js:
                        raw_prices = json.loads(prices_js)
                        for symbol, price in raw_prices.items():
                            asset = REVERSE_MAP.get(symbol, symbol)
                            live_prices[asset] = float(price)

                    if candles_js:
                        raw_candles = json.loads(candles_js)
                        for symbol, candles in raw_candles.items():
                            asset = REVERSE_MAP.get(symbol, symbol)
                            candle_history[asset] = candles

                    if live_prices:
                        ws_connected = True

                except Exception as e:
                    print(f"Price poll error: {e}")

                time.sleep(2)

        except ImportError:
            print("Selenium not installed!")
            ws_connected = False
            time.sleep(30)
        except Exception as e:
            print(f"Selenium error: {e}")
            ws_connected = False
            time.sleep(10)

def start_websocket():
    t = threading.Thread(target=_selenium_loop, daemon=True)
    t.start()
    print("Selenium price feed thread started!")

# Railway Chrome path helper
def get_chrome_options():
    from selenium.webdriver.chrome.options import Options
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.binary_location = "/usr/bin/chromium"
    return options
