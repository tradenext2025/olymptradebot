# ─── ALL TELEGRAM KEYBOARDS ───────────────────────────────────────────────────
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from config import ASSETS, TIMEFRAMES, DURATIONS, LANGUAGES
from languages import t

# ── LANGUAGE SELECTION ────────────────────────────────────────────────────────
def lang_keyboard():
    flags = {"en":"🇬🇧","sw":"🇹🇿","fr":"🇫🇷","ar":"🇸🇦","pt":"🇧🇷","es":"🇪🇸"}
    buttons, row = [], []
    for code, name in LANGUAGES.items():
        row.append(InlineKeyboardButton(f"{flags.get(code,'')} {name}", callback_data=f"lang_{code}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row: buttons.append(row)
    return InlineKeyboardMarkup(buttons)

# ── MAIN MENU ─────────────────────────────────────────────────────────────────
def main_menu_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"📊 {t(lang,'get_signal')}",  callback_data="menu_signal"),
            InlineKeyboardButton(f"🤖 {t(lang,'auto_signal')}", callback_data="menu_auto"),
        ],
        [
            InlineKeyboardButton(f"👤 {t(lang,'my_account')}",  callback_data="menu_account"),
            InlineKeyboardButton(f"⚙️ {t(lang,'settings')}",   callback_data="menu_settings"),
        ],
        [
            InlineKeyboardButton(f"📡 {t(lang,'status')}",      callback_data="menu_status"),
            InlineKeyboardButton(f"❓ {t(lang,'help')}",        callback_data="menu_help"),
        ],
        [
            InlineKeyboardButton(f"🌍 Language",                callback_data="menu_lang"),
            InlineKeyboardButton(f"🔐 Login OlympTrade",        callback_data="menu_login"),
        ],
    ])

# ── SIGNAL MODE ───────────────────────────────────────────────────────────────
def signal_mode_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"⚡ {t(lang,'immediate')}",  callback_data="mode_immediate"),
            InlineKeyboardButton(f"🔄 {t(lang,'auto_mode')}",  callback_data="mode_auto"),
        ],
        [
            InlineKeyboardButton(f"🏠 {t(lang,'home')}",       callback_data="menu_home"),
        ],
    ])

# ── ASSET CATEGORIES ──────────────────────────────────────────────────────────
def asset_category_keyboard(lang="en"):
    buttons = []
    for key, val in ASSETS.items():
        buttons.append([InlineKeyboardButton(
            f"{val['emoji']} {val['label']}",
            callback_data=f"cat_{key}"
        )])
    buttons.append([
        InlineKeyboardButton("🎲 Random Asset",  callback_data="asset_RANDOM"),
        InlineKeyboardButton("🔥 Best Signal",   callback_data="asset_BEST"),
    ])
    buttons.append([
        InlineKeyboardButton(f"🏠 {t(lang,'home')}", callback_data="menu_home"),
    ])
    return InlineKeyboardMarkup(buttons)

# ── ASSET LIST ────────────────────────────────────────────────────────────────
def asset_list_keyboard(cat_key, lang="en"):
    pairs = ASSETS[cat_key]["pairs"]
    buttons, row = [], []
    for pair in pairs:
        row.append(InlineKeyboardButton(pair, callback_data=f"asset_{pair}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([
        InlineKeyboardButton(f"🔙 {t(lang,'back')}", callback_data="back_categories"),
        InlineKeyboardButton(f"🏠 {t(lang,'home')}", callback_data="menu_home"),
    ])
    return InlineKeyboardMarkup(buttons)

# ── TIMEFRAME ─────────────────────────────────────────────────────────────────
def timeframe_keyboard(asset, lang="en"):
    tfs = list(TIMEFRAMES.keys())
    buttons, row = [], []
    for tf in tfs:
        row.append(InlineKeyboardButton(tf, callback_data=f"tf_{asset}|{tf}"))
        if len(row) == 3:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([
        InlineKeyboardButton(f"🔙 {t(lang,'back')}", callback_data="back_categories"),
        InlineKeyboardButton(f"🏠 {t(lang,'home')}", callback_data="menu_home"),
    ])
    return InlineKeyboardMarkup(buttons)

# ── DURATION ──────────────────────────────────────────────────────────────────
def duration_keyboard(asset, tf, lang="en"):
    buttons, row = [], []
    for dur in DURATIONS:
        row.append(InlineKeyboardButton(dur, callback_data=f"dur_{asset}|{tf}|{dur}"))
        if len(row) == 2:
            buttons.append(row); row = []
    if row: buttons.append(row)
    buttons.append([
        InlineKeyboardButton(f"🔙 {t(lang,'back')}", callback_data=f"asset_{asset}"),
        InlineKeyboardButton(f"🏠 {t(lang,'home')}", callback_data="menu_home"),
    ])
    return InlineKeyboardMarkup(buttons)

# ── SIGNAL RESULT ─────────────────────────────────────────────────────────────
def signal_result_keyboard(asset, tf, duration, lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"🔄 {t(lang,'new_signal')}",   callback_data=f"dur_{asset}|{tf}|{duration}"),
            InlineKeyboardButton(f"⏱ {t(lang,'change_timer')}",  callback_data=f"tf_{asset}|{tf}"),
        ],
        [
            InlineKeyboardButton(f"💼 {t(lang,'change_asset')}",  callback_data="back_categories"),
            InlineKeyboardButton(f"✅ {t(lang,'confirm_trade')}",  callback_data=f"trade_{asset}|{tf}|{duration}"),
        ],
        [
            InlineKeyboardButton(f"🏠 {t(lang,'home')}",          callback_data="menu_home"),
        ],
    ])

# ── TRADE CONFIRM ─────────────────────────────────────────────────────────────
def trade_confirm_keyboard(asset, tf, duration, direction, lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(f"✅ {t(lang,'yes_trade')}",  callback_data=f"confirm_yes_{asset}|{tf}|{duration}|{direction}"),
            InlineKeyboardButton(f"❌ {t(lang,'no_trade')}",   callback_data="confirm_no"),
        ],
    ])

# ── AUTO SIGNAL ───────────────────────────────────────────────────────────────
def auto_signal_keyboard(is_on, lang="en"):
    toggle = f"🔴 Stop Auto" if is_on else f"🟢 Start Auto"
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(toggle, callback_data="auto_toggle")],
        [
            InlineKeyboardButton("⚙️ Configure", callback_data="auto_config"),
            InlineKeyboardButton(f"🏠 {t(lang,'home')}", callback_data="menu_home"),
        ],
    ])

# ── SETTINGS ──────────────────────────────────────────────────────────────────
def settings_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Change Language",   callback_data="menu_lang")],
        [InlineKeyboardButton("🔔 Notifications",     callback_data="settings_notif")],
        [InlineKeyboardButton("💰 Default Amount",    callback_data="settings_amount")],
        [InlineKeyboardButton("⏱ Default Duration",  callback_data="settings_duration")],
        [InlineKeyboardButton(f"🏠 {t(lang,'home')}", callback_data="menu_home")],
    ])

# ── ACCOUNT ───────────────────────────────────────────────────────────────────
def account_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Login OlympTrade",   callback_data="menu_login")],
        [InlineKeyboardButton("💰 Check Balance",      callback_data="account_balance")],
        [InlineKeyboardButton("📊 Trade History",      callback_data="account_history")],
        [InlineKeyboardButton("🔓 Logout",             callback_data="account_logout")],
        [InlineKeyboardButton(f"🏠 {t(lang,'home')}",  callback_data="menu_home")],
    ])

# ── HOME BUTTON ONLY ──────────────────────────────────────────────────────────
def home_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"🏠 {t(lang,'home')}", callback_data="menu_home")],
    ])

# ── TRADE HISTORY KEYBOARD ────────────────────────────────────────────────────
def history_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 Win Rate",      callback_data="history_winrate"),
            InlineKeyboardButton("🔄 Refresh",        callback_data="history_refresh"),
        ],
        [
            InlineKeyboardButton("✅ Mark WIN",       callback_data="history_win"),
            InlineKeyboardButton("❌ Mark LOSS",      callback_data="history_loss"),
        ],
        [
            InlineKeyboardButton("🗑 Clear History",  callback_data="history_clear"),
            InlineKeyboardButton(f"🏠 Home",          callback_data="menu_home"),
        ],
    ])

# ── SIGNAL RESULT WITH MARK ───────────────────────────────────────────────────
def signal_result_with_mark_keyboard(asset, tf, duration, trade_id, lang="en"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ WIN",   callback_data=f"mark_win_{trade_id}"),
            InlineKeyboardButton("❌ LOSS",  callback_data=f"mark_loss_{trade_id}"),
        ],
        [
            InlineKeyboardButton("🔄 New Signal",   callback_data=f"dur_{asset}|{tf}|{duration}"),
            InlineKeyboardButton("⏱ Change Timer",  callback_data=f"tf_{asset}|{tf}"),
        ],
        [
            InlineKeyboardButton("💼 Change Asset",  callback_data="back_categories"),
            InlineKeyboardButton("✅ Confirm Trade",  callback_data=f"trade_{asset}|{tf}|{duration}"),
        ],
        [
            InlineKeyboardButton("🏠 Home",          callback_data="menu_home"),
        ],
    ])

# ── UPDATED ACCOUNT KEYBOARD ──────────────────────────────────────────────────
def account_keyboard_full(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔐 Login OlympTrade",   callback_data="menu_login")],
        [InlineKeyboardButton("💰 Check Balance",      callback_data="account_balance")],
        [InlineKeyboardButton("📊 Trade History",      callback_data="account_history")],
        [InlineKeyboardButton("📈 Win Rate",           callback_data="account_winrate")],
        [InlineKeyboardButton("🔓 Logout",             callback_data="account_logout")],
        [InlineKeyboardButton(f"🏠 Home",              callback_data="menu_home")],
    ])
