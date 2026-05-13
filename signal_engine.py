# ─── SIGNAL ENGINE (24/7 Analysis) ────────────────────────────────────────────
import time
import random
import threading
from datetime import datetime
from indicators import analyze
from config import ALL_PAIRS, TIMEFRAMES, AUTO_SIGNAL_INTERVAL

# ── STORAGE ───────────────────────────────────────────────────────────────────
# Stores latest signal per asset per timeframe
latest_signals = {}   # { "EURUSD_1m": { signal_dict } }
auto_users     = {}   # { user_id: { "asset": ..., "tf": ..., "dur": ..., "lang": ... } }
user_langs     = {}   # { user_id: "en" }
user_sessions  = {}   # { user_id: { "asset": ..., "tf": ..., "dur": ... } }

# ── BACKGROUND ANALYZER ───────────────────────────────────────────────────────
_running = False
_thread  = None

def _analyze_loop():
    global _running
    while _running:
        for asset in ALL_PAIRS:
            for tf_name in TIMEFRAMES:
                try:
                    sig = analyze(asset, tf_name)
                    key = f"{asset}_{tf_name}"
                    latest_signals[key] = {
                        **sig,
                        "analyzed_at": datetime.now().strftime("%H:%M:%S"),
                    }
                except Exception as e:
                    pass
            time.sleep(0.05)   # small delay between assets
        time.sleep(5)          # re-analyze every 5 seconds

def start_engine():
    global _running, _thread
    if not _running:
        _running = True
        _thread  = threading.Thread(target=_analyze_loop, daemon=True)
        _thread.start()
        print("Signal engine started - analyzing 24/7")

def stop_engine():
    global _running
    _running = False
    print("Signal engine stopped")

# ── GET SIGNAL ────────────────────────────────────────────────────────────────
def get_signal(asset, timeframe="1m"):
    key = f"{asset}_{timeframe}"
    if key in latest_signals:
        return latest_signals[key]
    # Generate fresh if not cached yet
    sig = analyze(asset, timeframe)
    sig["analyzed_at"] = datetime.now().strftime("%H:%M:%S")
    latest_signals[key] = sig
    return sig

def get_best_signal(timeframe="1m"):
    best = None
    best_prob = 0
    for asset in ALL_PAIRS:
        sig = get_signal(asset, timeframe)
        if sig["win_prob"] > best_prob:
            best_prob = sig["win_prob"]
            best = sig
    return best

# ── AUTO SIGNAL MANAGER ───────────────────────────────────────────────────────
def register_auto_user(user_id, asset, timeframe, duration, lang):
    auto_users[user_id] = {
        "asset":     asset,
        "timeframe": timeframe,
        "duration":  duration,
        "lang":      lang,
        "last_sent": 0,
    }

def unregister_auto_user(user_id):
    auto_users.pop(user_id, None)

def is_auto_user(user_id):
    return user_id in auto_users

def get_auto_users():
    return auto_users

def get_due_auto_users():
    now  = time.time()
    due  = []
    for uid, data in auto_users.items():
        if now - data["last_sent"] >= AUTO_SIGNAL_INTERVAL:
            due.append((uid, data))
    return due

def mark_sent(user_id):
    if user_id in auto_users:
        auto_users[user_id]["last_sent"] = time.time()

# ── USER SESSION ──────────────────────────────────────────────────────────────
def set_user_lang(user_id, lang):
    user_langs[user_id] = lang

def get_user_lang(user_id):
    return user_langs.get(user_id, "en")

def set_user_session(user_id, key, value):
    if user_id not in user_sessions:
        user_sessions[user_id] = {}
    user_sessions[user_id][key] = value

def get_user_session(user_id, key, default=None):
    return user_sessions.get(user_id, {}).get(key, default)

# ── FORMAT SIGNAL TEXT ────────────────────────────────────────────────────────
def format_signal_text(sig, duration, lang="en"):
    from languages import t
    now = datetime.now()
    direction = sig["direction"]
    arrow = "📈" if direction == "BUY" else "📉"
    dir_text = t(lang, "direction_buy") if direction == "BUY" else t(lang, "direction_sell")
    reasons = "\n".join([f"  • {r}" for r in sig.get("reasons", [])[:3]])

    return (
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 *{t(lang, 'signal_title')}*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"{arrow} *{t(lang, 'choose_asset')[:-1]}:* `{sig['asset']}`\n"
        f"💹 *Direction:* *{dir_text}*\n"
        f"💰 *{t(lang, 'entry_price')}:* `{sig['price_str']}`\n"
        f"⏰ *{t(lang, 'entry_time')}:* `{now.strftime('%H:%M:%S')}`\n"
        f"📅 *Date:* `{now.strftime('%d/%m/%Y')}`\n"
        f"⏱ *{t(lang, 'duration')}:* `{duration}`\n"
        f"📊 *{t(lang, 'win_prob')}:* `{sig['win_prob']}%`\n"
        f"💪 *{t(lang, 'strength')}:* `{sig['strength']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"📉 *BB:* `U={sig['bb_upper']} M={sig['bb_middle']} L={sig['bb_lower']}`\n"
        f"📊 *Stoch:* `K={sig['k']} D={sig['d']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🔍 *Analysis:*\n{reasons}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"⚡ _{t(lang, 'risk')}_\n"
        f"🤖 _Nexus DTrader Pro_"
    )
