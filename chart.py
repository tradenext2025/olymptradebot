# ─── CHART GENERATOR (Candles + BB + Stochastic) ──────────────────────────────
import io
import random
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont

# ── COLORS ────────────────────────────────────────────────────────────────────
BG_COLOR      = (13, 17, 23)       # Dark background
GREEN         = (0, 220, 100)      # Bullish candle
RED           = (255, 59, 59)      # Bearish candle
BB_UPPER_COL  = (255, 165, 0)      # Orange
BB_MID_COL    = (100, 149, 237)    # Blue
BB_LOWER_COL  = (255, 165, 0)      # Orange
STOCH_K_COL   = (100, 200, 255)    # Light blue
STOCH_D_COL   = (255, 140, 0)      # Orange
GRID_COL      = (30, 35, 45)       # Dark grid
TEXT_COL      = (200, 200, 200)    # Light text
WHITE         = (255, 255, 255)
YELLOW        = (255, 215, 0)

def draw_chart(signal: dict) -> io.BytesIO:
    candles  = signal["candles"][-40:]   # last 40 candles
    bb       = signal["bb"][-40:]
    k_vals   = signal["k_vals"][-40:]
    d_vals   = signal["d_vals"][-40:]
    asset    = signal["asset"]
    direction = signal["direction"]
    win_prob  = signal["win_prob"]
    strength  = signal["strength"]
    price_str = signal["price_str"]
    timeframe = signal.get("timeframe", "1m")

    # ── Canvas ────────────────────────────────────────────────────────────────
    W, H        = 900, 620
    CHART_TOP   = 80
    CHART_H     = 340
    STOCH_TOP   = CHART_TOP + CHART_H + 30
    STOCH_H     = 120
    PADDING_L   = 60
    PADDING_R   = 20
    chart_w     = W - PADDING_L - PADDING_R

    img  = Image.new("RGB", (W, H), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    try:
        font_big    = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 36)
        font_med    = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf", 18)
        font_small  = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 13)
        font_tiny   = ImageFont.truetype("/usr/share/fonts/dejavu/DejaVuSans.ttf", 11)
    except:
        font_big   = ImageFont.load_default()
        font_med   = ImageFont.load_default()
        font_small = ImageFont.load_default()
        font_tiny  = ImageFont.load_default()

    # ── Header ────────────────────────────────────────────────────────────────
    draw.rectangle([(0, 0), (W, 55)], fill=(20, 25, 35))
    draw.text((15, 10), f"NEXUS SIGNAL  |  {asset}  |  {timeframe}", font=font_med, fill=YELLOW)
    draw.text((15, 32), f"Price: {price_str}  |  {datetime.now().strftime('%H:%M:%S %d/%m/%Y')}", font=font_small, fill=TEXT_COL)

    # ── BUY/SELL badge ────────────────────────────────────────────────────────
    badge_color = (0, 180, 80) if direction == "BUY" else (200, 40, 40)
    badge_x = W - 220
    draw.rounded_rectangle([(badge_x, 8), (W - 15, 48)], radius=8, fill=badge_color)
    draw.text((badge_x + 15, 12), f"{'📈' if direction == 'BUY' else '📉'} {direction}", font=font_big, fill=WHITE)

    # ── Price chart area ──────────────────────────────────────────────────────
    closes = [c["close"] for c in candles]
    highs  = [c["high"]  for c in candles]
    lows   = [c["low"]   for c in candles]
    bb_uppers = [b["upper"] for b in bb if b["upper"]]
    bb_lowers = [b["lower"] for b in bb if b["lower"]]

    all_prices = closes + highs + lows
    if bb_uppers: all_prices += bb_uppers
    if bb_lowers: all_prices += bb_lowers

    price_min = min(all_prices) * 0.9995
    price_max = max(all_prices) * 1.0005
    price_range = price_max - price_min if price_max != price_min else 1

    def price_to_y(p):
        return int(CHART_TOP + CHART_H - ((p - price_min) / price_range) * CHART_H)

    # Grid lines
    for i in range(5):
        y = CHART_TOP + int(i * CHART_H / 4)
        draw.line([(PADDING_L, y), (W - PADDING_R, y)], fill=GRID_COL, width=1)
        p = price_max - (i / 4) * price_range
        label = f"{p:,.2f}" if p > 100 else f"{p:.5f}"
        draw.text((2, y - 7), label, font=font_tiny, fill=TEXT_COL)

    # Candle width
    n       = len(candles)
    c_w     = max(4, int(chart_w / n) - 2)
    spacing = chart_w / n

    # Draw Bollinger Bands (fill between upper and lower)
    bb_points_upper = []
    bb_points_lower = []
    for i, b in enumerate(bb):
        if b["upper"] and b["lower"]:
            x = int(PADDING_L + i * spacing + spacing / 2)
            bb_points_upper.append((x, price_to_y(b["upper"])))
            bb_points_lower.append((x, price_to_y(b["lower"])))

    # Fill BB band
    if len(bb_points_upper) > 1:
        poly = bb_points_upper + list(reversed(bb_points_lower))
        draw.polygon(poly, fill=(255, 165, 0, 20))

    # Draw BB lines
    for i in range(1, len(bb)):
        if bb[i]["upper"] and bb[i-1]["upper"]:
            x1 = int(PADDING_L + (i-1) * spacing + spacing/2)
            x2 = int(PADDING_L + i     * spacing + spacing/2)
            draw.line([(x1, price_to_y(bb[i-1]["upper"])), (x2, price_to_y(bb[i]["upper"]))], fill=BB_UPPER_COL, width=1)
            draw.line([(x1, price_to_y(bb[i-1]["middle"])), (x2, price_to_y(bb[i]["middle"]))], fill=BB_MID_COL, width=1)
            draw.line([(x1, price_to_y(bb[i-1]["lower"])), (x2, price_to_y(bb[i]["lower"]))], fill=BB_LOWER_COL, width=1)

    # Draw candles
    for i, c in enumerate(candles):
        x     = int(PADDING_L + i * spacing)
        cx    = x + int(spacing / 2)
        color = GREEN if c["close"] >= c["open"] else RED

        # Wick
        draw.line([(cx, price_to_y(c["high"])), (cx, price_to_y(c["low"]))], fill=color, width=1)

        # Body
        y_open  = price_to_y(c["open"])
        y_close = price_to_y(c["close"])
        y_top   = min(y_open, y_close)
        y_bot   = max(y_open, y_close)
        if y_bot - y_top < 1: y_bot = y_top + 1
        draw.rectangle([(cx - c_w//2, y_top), (cx + c_w//2, y_bot)], fill=color)

    # ── Stochastic panel ──────────────────────────────────────────────────────
    draw.rectangle([(PADDING_L, STOCH_TOP), (W - PADDING_R, STOCH_TOP + STOCH_H)], fill=(18, 22, 30))
    draw.text((PADDING_L + 5, STOCH_TOP - 18), "Stochastic Oscillator", font=font_small, fill=TEXT_COL)

    # Overbought/Oversold lines
    ob_y = int(STOCH_TOP + STOCH_H * (1 - 80/100))
    os_y = int(STOCH_TOP + STOCH_H * (1 - 20/100))
    draw.line([(PADDING_L, ob_y), (W - PADDING_R, ob_y)], fill=(255, 80, 80), width=1)
    draw.line([(PADDING_L, os_y), (W - PADDING_R, os_y)], fill=(80, 255, 80), width=1)
    draw.text((W - PADDING_R + 2, ob_y - 7), "80", font=font_tiny, fill=(255, 80, 80))
    draw.text((W - PADDING_R + 2, os_y - 7), "20", font=font_tiny, fill=(80, 255, 80))

    def stoch_to_y(v):
        return int(STOCH_TOP + STOCH_H - (v / 100) * STOCH_H)

    # Draw K and D lines
    for i in range(1, len(k_vals)):
        if k_vals[i] and k_vals[i-1]:
            x1 = int(PADDING_L + (i-1) * spacing + spacing/2)
            x2 = int(PADDING_L + i     * spacing + spacing/2)
            draw.line([(x1, stoch_to_y(k_vals[i-1])), (x2, stoch_to_y(k_vals[i]))], fill=STOCH_K_COL, width=2)
        if d_vals[i] and d_vals[i-1]:
            x1 = int(PADDING_L + (i-1) * spacing + spacing/2)
            x2 = int(PADDING_L + i     * spacing + spacing/2)
            draw.line([(x1, stoch_to_y(d_vals[i-1])), (x2, stoch_to_y(d_vals[i]))], fill=STOCH_D_COL, width=2)

    # Stochastic legend
    draw.rectangle([(PADDING_L + 5, STOCH_TOP + STOCH_H - 20), (PADDING_L + 15, STOCH_TOP + STOCH_H - 12)], fill=STOCH_K_COL)
    draw.text((PADDING_L + 18, STOCH_TOP + STOCH_H - 22), f"K={k_vals[-1] or 'N/A'}", font=font_tiny, fill=STOCH_K_COL)
    draw.rectangle([(PADDING_L + 70, STOCH_TOP + STOCH_H - 20), (PADDING_L + 80, STOCH_TOP + STOCH_H - 12)], fill=STOCH_D_COL)
    draw.text((PADDING_L + 83, STOCH_TOP + STOCH_H - 22), f"D={d_vals[-1] or 'N/A'}", font=font_tiny, fill=STOCH_D_COL)

    # ── Footer info ───────────────────────────────────────────────────────────
    footer_y = STOCH_TOP + STOCH_H + 10
    win_color = (0, 220, 100) if win_prob >= 80 else (255, 165, 0) if win_prob >= 70 else (255, 80, 80)

    draw.text((PADDING_L, footer_y), f"Win Probability: {win_prob}%", font=font_med, fill=win_color)
    draw.text((PADDING_L + 260, footer_y), f"Strength: {strength}", font=font_med, fill=YELLOW)
    draw.text((PADDING_L, footer_y + 22), "BB Legend:", font=font_tiny, fill=TEXT_COL)
    draw.rectangle([(PADDING_L + 75, footer_y + 24), (PADDING_L + 90, footer_y + 32)], fill=BB_UPPER_COL)
    draw.text((PADDING_L + 93, footer_y + 22), "Upper/Lower", font=font_tiny, fill=BB_UPPER_COL)
    draw.rectangle([(PADDING_L + 175, footer_y + 24), (PADDING_L + 190, footer_y + 32)], fill=BB_MID_COL)
    draw.text((PADDING_L + 193, footer_y + 22), "Middle", font=font_tiny, fill=BB_MID_COL)
    draw.text((W - 200, footer_y + 5), "Nexus DTrader Pro", font=font_small, fill=(80, 80, 120))

    # ── Save to buffer ────────────────────────────────────────────────────────
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
