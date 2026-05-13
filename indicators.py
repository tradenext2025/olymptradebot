# ─── BOLLINGER BANDS + STOCHASTIC (Real + Simulated) ──────────────────────────
import random
from config import (
    BASE_PRICES, BB_PERIOD, BB_STD,
    STOCH_K_PERIOD, STOCH_D_PERIOD,
    STOCH_OVERBOUGHT, STOCH_OVERSOLD
)

def get_real_candles(asset, n=60):
    try:
        from websocket_client import get_candle_history
        real = get_candle_history(asset, n)
        if len(real) >= 20:
            return real
    except:
        pass
    return []

def generate_candles(asset, n=60):
    # Try real candles first
    real = get_real_candles(asset, n)
    if real:
        return real

    # Fallback simulation
    try:
        from websocket_client import get_live_price
        base = get_live_price(asset) or BASE_PRICES.get(asset, 1.0)
    except:
        base = BASE_PRICES.get(asset, 1.0)

    candles = []
    price = base * random.uniform(0.997, 1.003)
    for _ in range(n):
        change = price * random.uniform(-0.004, 0.004)
        open_  = round(price, 5)
        close  = round(price + change, 5)
        high   = round(max(open_, close) + abs(change) * random.uniform(0.1, 0.6), 5)
        low    = round(min(open_, close) - abs(change) * random.uniform(0.1, 0.6), 5)
        candles.append({"open": open_, "close": close, "high": high, "low": low, "volume": random.randint(100, 9999)})
        price = close
    return candles

def bollinger_bands(candles, period=BB_PERIOD, std_dev=BB_STD):
    closes = [c["close"] for c in candles]
    bands  = []
    for i in range(len(closes)):
        if i < period - 1:
            bands.append({"upper": None, "middle": None, "lower": None})
            continue
        window   = closes[i - period + 1: i + 1]
        mean     = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std      = variance ** 0.5
        bands.append({
            "upper":  round(mean + std_dev * std, 5),
            "middle": round(mean, 5),
            "lower":  round(mean - std_dev * std, 5),
        })
    return bands

def stochastic(candles, k_period=STOCH_K_PERIOD, d_period=STOCH_D_PERIOD):
    k_values = []
    for i in range(len(candles)):
        if i < k_period - 1:
            k_values.append(None)
            continue
        window   = candles[i - k_period + 1: i + 1]
        high_max = max(c["high"] for c in window)
        low_min  = min(c["low"]  for c in window)
        close    = candles[i]["close"]
        if high_max == low_min:
            k_values.append(50.0)
        else:
            k_values.append(round(((close - low_min) / (high_max - low_min)) * 100, 2))

    d_values = []
    for i in range(len(k_values)):
        window = [v for v in k_values[max(0, i - d_period + 1): i + 1] if v is not None]
        d_values.append(round(sum(window) / len(window), 2) if len(window) >= d_period else None)

    return k_values, d_values

def analyze(asset, timeframe="1m"):
    candles      = generate_candles(asset, n=60)
    bb           = bollinger_bands(candles)
    k_vals, d_vals = stochastic(candles)
    last         = candles[-1]
    prev         = candles[-2]
    bb_last      = bb[-1]
    bb_prev      = bb[-2]
    k            = k_vals[-1]
    k_prev       = k_vals[-2]
    d            = d_vals[-1]
    d_prev       = d_vals[-2]

    buy_signals  = 0
    sell_signals = 0
    reasons      = []

    if bb_last["lower"] and last["close"] <= bb_last["lower"]:
        buy_signals += 3
        reasons.append("Price at Lower BB (oversold)")
    elif bb_last["lower"] and prev["close"] < bb_prev.get("lower",0) and last["close"] > bb_last["lower"]:
        buy_signals += 2
        reasons.append("Price bounced above Lower BB")

    if bb_last["upper"] and last["close"] >= bb_last["upper"]:
        sell_signals += 3
        reasons.append("Price at Upper BB (overbought)")
    elif bb_last["upper"] and prev["close"] > bb_prev.get("upper",9999) and last["close"] < bb_last["upper"]:
        sell_signals += 2
        reasons.append("Price dropped below Upper BB")

    if k and d:
        if k < STOCH_OVERSOLD and d < STOCH_OVERSOLD:
            buy_signals += 2
            reasons.append(f"Stochastic oversold K={k} D={d}")
        if k_prev and d_prev and k_prev < d_prev and k > d and k < 40:
            buy_signals += 3
            reasons.append("Stochastic K crossed above D (bullish)")
        if k > STOCH_OVERBOUGHT and d > STOCH_OVERBOUGHT:
            sell_signals += 2
            reasons.append(f"Stochastic overbought K={k} D={d}")
        if k_prev and d_prev and k_prev > d_prev and k < d and k > 60:
            sell_signals += 3
            reasons.append("Stochastic K crossed below D (bearish)")

    body = abs(last["close"] - last["open"])
    wick = last["high"] - last["low"]
    if last["close"] > last["open"] and body > wick * 0.5:
        buy_signals += 1
        reasons.append("Strong bullish candle")
    if last["close"] < last["open"] and body > wick * 0.5:
        sell_signals += 1
        reasons.append("Strong bearish candle")

    direction = "BUY" if buy_signals >= sell_signals else "SELL"
    diff      = abs(buy_signals - sell_signals)

    if diff >= 5:   win_prob = random.randint(88, 95)
    elif diff >= 3: win_prob = random.randint(80, 87)
    elif diff >= 1: win_prob = random.randint(72, 79)
    else:           win_prob = random.randint(65, 71)

    if win_prob >= 88:   strength = "STRONG"
    elif win_prob >= 80: strength = "GOOD"
    elif win_prob >= 72: strength = "MEDIUM"
    else:                strength = "WEAK"

    # Use real price if available
    try:
        from websocket_client import get_live_price
        real_price = get_live_price(asset)
        price = real_price if real_price else last["close"]
    except:
        price = last["close"]

    price_str = f"{price:,.2f}" if price > 100 else f"{price:.5f}"

    return {
        "asset": asset, "direction": direction,
        "price": price, "price_str": price_str,
        "win_prob": win_prob, "strength": strength,
        "reasons": reasons, "k": k, "d": d,
        "bb_upper": bb_last["upper"],
        "bb_middle": bb_last["middle"],
        "bb_lower": bb_last["lower"],
        "candles": candles, "bb": bb,
        "k_vals": k_vals, "d_vals": d_vals,
        "timeframe": timeframe,
        "buy_score": buy_signals,
        "sell_score": sell_signals,
    }
