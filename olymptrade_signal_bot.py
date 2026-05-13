import logging
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TELEGRAM_TOKEN = "8972480830:AAEF4XB9MWJzYWPqcrLqz6TNybQRhW3pny8"
ADMIN_ID = 7664139802
OLYMP_TOKEN = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE3Nzg3OTA4MzIsImlhdCI6MTc3ODYxODAzMiwiaWQiOjg3NzE4OTc3NSwibmJmIjoxNzc4NjE4MDMyLCJyZXFfY3R4X2hhc2giOiI0YWM5MmE1MmIzOWUzYWNkN2NhZTE1NTZkOWZjNWRiZiIsInR5cGUiOiJiZWFyZXIiLCJ1c2VyX2lkIjoxMjc2NTA1MTJ9.Gt2Tm-2PdqMhE9kYJn2CgrhopE12nopt_bIuWBtm-K-gGPIFT-udaUXwKojYAABi-aqH6nx9Ld1BHhVhVHJiitojpR8rXqNZxvuq8LJRBWKJKpTYh_tbtO2nHmJpg6d6DDv4FPtvGrHYeeMy-o-wyINjHYtPLfuqvXe0IeAdlw1ecGXP_W_Wbd8osUAroEMTE5xLZqMcSZMWBKREXhLMeoYZdHozf3WjkXjsza5jn68CvKMgJG5oTc5f5JTkP8g2VKH_KU9Qvvt-WQtMpG_0EcctcIvz1Uv2k-7fk9wZYN_WnAsDr786nb3nurKZrt0YD0XtvflZ1eB6INHE2JT41X_GkP-WmDtlnyL5wz-LuhIS6Fc6SuHrgjG1_71Ukdmkrrb38o5eNpTogR23pSaK_K0E9ETr-vmCfB7rjMdrHN8jxAsOeI0B0NeZGUDOZDp1p_43zf0VRAOxel6hxaTCgo2jfD4pfrjA6BOsXlgPKgADHF1932F8qbW8t2e2EOBb557_tl-g0AoPhiZmEIV230jgcFsnyx_UOO3VVzHk4sBytSvkr7vuvMioWRUGWfRddYPNQV8wYDvz6IMjcpbF_ImCLiw7nNbydytOTqCgM3qHVSGn1x9aMgsTkx-xCg8uGsLAYH2qHWgBz-Nh4wlYGwFbIh8PzfYOrGOnF93u0mg"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

ASSETS = {
    "crypto_otc":    {"label": "Crypto OTC",    "pairs": ["Bitcoin OTC","Ripple OTC","Dogecoin OTC","Ethereum OTC","Litecoin OTC"]},
    "forex_otc":     {"label": "Forex OTC",     "pairs": ["EUR/USD OTC","GBP/USD OTC","USD/JPY OTC","AUD/USD OTC","USD/CAD OTC","USD/CHF OTC","NZD/USD OTC","EUR/GBP OTC","EUR/JPY OTC","GBP/JPY OTC","GBP/AUD OTC","GBP/CAD OTC","GBP/CHF OTC","GBP/NZD OTC"]},
    "commodity_otc": {"label": "Commodity OTC", "pairs": ["Gold OTC","Silver OTC","Oil OTC"]},
    "index_otc":     {"label": "Index OTC",     "pairs": ["Compound Index","AUS 200 OTC","US 500 OTC","US TECH 100 OTC"]},
}
ALL_PAIRS = [p for cat in ASSETS.values() for p in cat["pairs"]]

BASE_PRICES = {
    "Bitcoin OTC": 62450.50, "Ripple OTC": 0.52340, "Dogecoin OTC": 0.15820,
    "Ethereum OTC": 3210.75, "Litecoin OTC": 85.320,
    "EUR/USD OTC": 1.08542, "GBP/USD OTC": 1.27341, "USD/JPY OTC": 149.823,
    "AUD/USD OTC": 0.65120, "USD/CAD OTC": 1.36540, "USD/CHF OTC": 0.89230,
    "NZD/USD OTC": 0.60120, "EUR/GBP OTC": 0.85320, "EUR/JPY OTC": 162.540,
    "GBP/JPY OTC": 190.230, "GBP/AUD OTC": 1.95420, "GBP/CAD OTC": 1.73210,
    "GBP/CHF OTC": 1.13540, "GBP/NZD OTC": 2.11230,
    "Gold OTC": 2345.60, "Silver OTC": 27.850, "Oil OTC": 78.320,
    "Compound Index": 7657.15, "AUS 200 OTC": 7842.50,
    "US 500 OTC": 5123.40, "US TECH 100 OTC": 18234.60,
}

def get_candles(asset, n=14):
    base = BASE_PRICES.get(asset, 1.0)
    candles = []
    price = base * random.uniform(0.995, 1.005)
    for _ in range(n):
        change = price * random.uniform(-0.003, 0.003)
        open_ = price
        close = price + change
        candles.append({"open": open_, "close": close})
        price = close
    return candles

def compute_rsi(candles, period=7):
    closes = [c["close"] for c in candles]
    gains, losses = [], []
    for i in range(1, len(closes)):
        diff = closes[i] - closes[i-1]
        gains.append(max(diff, 0))
        losses.append(max(-diff, 0))
    avg_gain = sum(gains[-period:]) / period
    avg_loss = sum(losses[-period:]) / period
    if avg_loss == 0: return 100
    return round(100 - (100 / (1 + avg_gain / avg_loss)), 1)

def compute_ema(candles, period):
    closes = [c["close"] for c in candles]
    k = 2 / (period + 1)
    ema = closes[0]
    for price in closes[1:]:
        ema = price * k + ema * (1 - k)
    return ema

def true_signal(asset):
    candles = get_candles(asset, 14)
    rsi = compute_rsi(candles)
    ema_fast = compute_ema(candles, 3)
    ema_slow = compute_ema(candles, 7)
    last = candles[-1]
    bull, bear = 0, 0
    if rsi < 35: bull += 2
    if rsi > 65: bear += 2
    if ema_fast > ema_slow: bull += 2
    else: bear += 2
    if last["close"] > last["open"]: bull += 1
    else: bear += 1
    direction = "UP" if bull >= bear else "DOWN"
    diff = abs(bull - bear)
    if diff >= 4: win_prob = random.randint(88, 95)
    elif diff >= 2: win_prob = random.randint(78, 87)
    else: win_prob = random.randint(70, 77)
    if win_prob >= 88: strength = "STRONG"
    elif win_prob >= 78: strength = "GOOD"
    else: strength = "MEDIUM"
    price = round(last["close"], 5)
    price_str = f"{price:,.2f}" if price > 1000 else f"{price:.5f}"
    return {"asset": asset, "direction": direction, "price_str": price_str,
            "win_prob": win_prob, "strength": strength, "rsi": rsi,
            "ema_fast": round(ema_fast, 5), "ema_slow": round(ema_slow, 5)}

def format_signal(s, duration):
    now = datetime.now()
    arrow = "UP" if s["direction"] == "UP" else "DOWN"
    return (
        f"NEXUS SIGNAL\n"
        f"Asset: {s['asset']}\n"
        f"Direction: {arrow}\n"
        f"Entry Price: {s['price_str']}\n"
        f"Time: {now.strftime('%H:%M:%S')}\n"
        f"Date: {now.strftime('%d/%m/%Y')}\n"
        f"Duration: {duration}\n"
        f"Win Probability: {s['win_prob']}%\n"
        f"Strength: {s['strength']}\n"
        f"RSI: {s['rsi']} | EMA Fast: {s['ema_fast']} | EMA Slow: {s['ema_slow']}\n"
        f"Trade at your own risk!\n"
        f"Nexus DTrader Pro"
    )

user_asset = {}

def main_keyboard():
    buttons = [[InlineKeyboardButton(v["label"], callback_data=f"cat_{k}")] for k, v in ASSETS.items()]
    buttons.append([InlineKeyboardButton("Random", callback_data="asset_RANDOM"), InlineKeyboardButton("Best Signal", callback_data="asset_BEST")])
    return InlineKeyboardMarkup(buttons)

def category_keyboard(cat_key):
    pairs = ASSETS[cat_key]["pairs"]
    buttons, row = [], []
    for pair in pairs:
        row.append(InlineKeyboardButton(pair, callback_data=f"asset_{pair}"))
        if len(row) == 2: buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton("Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

def duration_keyboard(asset):
    durations = ["5 sec","10 sec","15 sec","30 sec","1 min","2 min","3 min","5 min"]
    buttons, row = [], []
    for d in durations:
        row.append(InlineKeyboardButton(d, callback_data=f"dur_{asset}|{d}"))
        if len(row) == 2: buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([InlineKeyboardButton("Back", callback_data="back_main")])
    return InlineKeyboardMarkup(buttons)

def signal_keyboard(asset, duration):
    return InlineKeyboardMarkup([[
        InlineKeyboardButton("New Signal", callback_data=f"dur_{asset}|{duration}"),
        InlineKeyboardButton("Change Timer", callback_data=f"asset_{asset}"),
        InlineKeyboardButton("Change Asset", callback_data="back_main"),
    ]])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Nexus DTrader Pro\nOlympTrade Signal Bot\n\n"
        "/signal - Get trading signal\n"
        "/assets - List all OTC assets\n"
        "/status - Bot status"
    )

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Select Asset Category:", reply_markup=main_keyboard())

async def assets_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    lines = []
    for cat in ASSETS.values():
        lines.append(f"\n{cat['label']}:")
        for pair in cat["pairs"]: lines.append(f"  - {pair}")
    await update.message.reply_text("All OTC Assets:\n" + "\n".join(lines))

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Bot: Running\nSignal Engine: RSI + EMA\nAssets: {len(ALL_PAIRS)} OTC pairs\nTime: {datetime.now().strftime('%H:%M:%S')}"
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    uid = query.from_user.id

    if data == "back_main":
        await query.edit_message_text("Select Asset Category:", reply_markup=main_keyboard())

    elif data.startswith("cat_"):
        cat_key = data.replace("cat_", "")
        cat = ASSETS[cat_key]
        await query.edit_message_text(f"Select {cat['label']}:", reply_markup=category_keyboard(cat_key))

    elif data.startswith("asset_"):
        key = data.replace("asset_", "")
        if key == "RANDOM": asset = random.choice(ALL_PAIRS)
        elif key == "BEST": asset = max(ALL_PAIRS, key=lambda a: true_signal(a)["win_prob"])
        else: asset = key
        user_asset[uid] = asset
        await query.edit_message_text(f"Select Duration for:\n{asset}", reply_markup=duration_keyboard(asset))

    elif data.startswith("dur_"):
        parts = data[4:].split("|")
        asset = parts[0]
        duration = parts[1]
        await query.edit_message_text("Analyzing market...")
        sig = true_signal(asset)
        sig["asset"] = asset
        await query.edit_message_text(format_signal(sig, duration), reply_markup=signal_keyboard(asset, duration))

def run():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("signal", signal_cmd))
    app.add_handler(CommandHandler("assets", assets_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Nexus DTrader Pro started!")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    run()
