# ─── REAL OLYMPTRADE PRICES using olymptrade_ws library ───────────────────────
import asyncio
import threading
import time
from config import OLYMP_TOKEN, BASE_PRICES

live_prices    = {}
candle_history = {}
ws_connected   = False
_client        = None

SYMBOL_MAP = {
    "Bitcoin OTC":     "BTCUSD",
    "Ripple OTC":      "XRPUSD",
    "Dogecoin OTC":    "DOGEUSD",
    "Ethereum OTC":    "ETHUSD",
    "Litecoin OTC":    "LTCUSD",
    "EUR/USD OTC":     "EURUSD",
    "GBP/USD OTC":     "GBPUSD",
    "USD/JPY OTC":     "USDJPY",
    "AUD/USD OTC":     "AUDUSD",
    "USD/CAD OTC":     "USDCAD",
    "USD/CHF OTC":     "USDCHF",
    "NZD/USD OTC":     "NZDUSD",
    "EUR/GBP OTC":     "EURGBP",
    "EUR/JPY OTC":     "EURJPY",
    "GBP/JPY OTC":     "GBPJPY",
    "GBP/AUD OTC":     "GBPAUD",
    "GBP/CAD OTC":     "GBPCAD",
    "GBP/CHF OTC":     "GBPCHF",
    "GBP/NZD OTC":     "GBPNZD",
    "Gold OTC":        "XAUUSD",
    "Silver OTC":      "XAGUSD",
    "Oil OTC":         "USOIL",
    "Compound Index":  "COMPOUND",
    "AUS 200 OTC":     "AUS200",
    "US 500 OTC":      "US500",
    "US TECH 100 OTC": "USTECH100",
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
        "open":   float(open_),
        "close":  float(close),
        "high":   float(high),
        "low":    float(low),
        "volume": int(volume),
    })
    if len(candle_history[asset]) > 300:
        candle_history[asset] = candle_history[asset][-300:]

# ── ASYNC PRICE LOOP ──────────────────────────────────────────────────────────
async def _run_client():
    global ws_connected, live_prices, _client
    while True:
        try:
            from olymptrade_ws import OlympTradeClient
            from olympconfig import parameters

            print("Connecting to OlympTrade real price feed...")
            _client = OlympTradeClient(access_token=OLYMP_TOKEN)

            # ── Tick callback ─────────────────────────────────────────────────
            async def on_tick(message):
                try:
                    ticks = message.get("d", [])
                    for tick in ticks:
                        pair  = tick.get("p", "")
                        price = tick.get("q")
                        ts    = tick.get("t", 0)
                        if pair and price:
                            asset = REVERSE_MAP.get(pair, None)
                            if asset:
                                p = float(price)
                                live_prices[asset] = p
                                _add_candle(asset, p, p, p, p)
                except Exception as e:
                    print(f"Tick error: {e}")

            # ── Candle callback ───────────────────────────────────────────────
            async def on_candle(message):
                try:
                    candles = message.get("d", [])
                    for c in candles:
                        pair = c.get("p", "")
                        asset = REVERSE_MAP.get(pair, None)
                        if asset and c.get("c"):
                            live_prices[asset] = float(c["c"])
                            _add_candle(
                                asset,
                                c.get("o", c["c"]),
                                c["c"],
                                c.get("h", c["c"]),
                                c.get("l", c["c"]),
                                c.get("v", 0)
                            )
                except Exception as e:
                    print(f"Candle error: {e}")

            _client.register_callback(parameters.E_TICK_UPDATE,   on_tick)
            _client.register_callback(parameters.E_CANDLE_UPDATE, on_candle)

            await _client.start()

            if _client.is_connected:
                ws_connected = True
                print("✅ Connected to OlympTrade real prices!")

                # Subscribe to all assets
                for asset_name, symbol in SYMBOL_MAP.items():
                    try:
                        await _client.market.subscribe_ticks(symbol)
                        await asyncio.sleep(0.05)
                    except Exception as e:
                        print(f"Subscribe error {symbol}: {e}")

                print(f"✅ Subscribed to {len(SYMBOL_MAP)} assets!")

                # Keep alive — check connection
                while _client.is_connected:
                    await asyncio.sleep(5)

                ws_connected = False
                print("WebSocket disconnected — reconnecting...")

            else:
                print("❌ Failed to connect to OlympTrade")
                ws_connected = False

        except ImportError:
            print("olymptrade_ws not installed — install with: pip install olymptrade-api")
            ws_connected = False
            await asyncio.sleep(30)
        except Exception as e:
            print(f"Price feed error: {e}")
            ws_connected = False
            await asyncio.sleep(10)

# ── START IN BACKGROUND THREAD ────────────────────────────────────────────────
def start_websocket():
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(_run_client())

    t = threading.Thread(target=run, daemon=True)
    t.start()
    print("Price feed thread started!")
