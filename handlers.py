# ─── BOT HANDLERS (FULLY FIXED v3) ────────────────────────────────────────────
import asyncio
import random
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from languages import t
from keyboards import (
    lang_keyboard, main_menu_keyboard, signal_mode_keyboard,
    asset_category_keyboard, asset_list_keyboard, timeframe_keyboard,
    duration_keyboard, settings_keyboard, account_keyboard, home_keyboard,
    history_keyboard
)
from signal_engine import (
    get_signal, get_best_signal, format_signal_text,
    set_user_lang, get_user_lang, set_user_session, get_user_session,
    register_auto_user, unregister_auto_user, is_auto_user
)
from chart import draw_chart
from config import ASSETS, ALL_PAIRS, ANALYSIS_TIME

def make_signal_keyboard(asset, tf, duration, trade_id=0):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ WIN",          callback_data=f"mark_win_{trade_id}"),
            InlineKeyboardButton("❌ LOSS",         callback_data=f"mark_loss_{trade_id}"),
        ],
        [
            InlineKeyboardButton("🔄 New Signal",   callback_data=f"dur_{asset}|{tf}|{duration}"),
            InlineKeyboardButton("⏱ Change Timer",  callback_data=f"tf_{asset}|{tf}"),
        ],
        [
            InlineKeyboardButton("💼 Change Asset",  callback_data="back_categories"),
            InlineKeyboardButton("✅ Confirm Trade", callback_data=f"trade_{asset}|{tf}|{duration}"),
        ],
        [
            InlineKeyboardButton("🛑 Stop Auto",    callback_data="auto_stop"),
            InlineKeyboardButton("🏠 Home",         callback_data="send_home"),
        ],
    ])

def make_auto_keyboard(is_on):
    if is_on:
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 STOP AUTO SIGNALS", callback_data="auto_stop")],
            [InlineKeyboardButton("🏠 Home", callback_data="send_home")],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("▶️ Start Auto", callback_data="auto_config")],
        [InlineKeyboardButton("🏠 Home",       callback_data="send_home")],
    ])

# ── SAFE EDIT OR SEND ──────────────────────────────────────────────────────────
async def safe_reply(query, text, keyboard, lang="en"):
    """Always sends a new message — avoids edit errors on photo messages"""
    try:
        await query.edit_message_text(
            text, parse_mode="Markdown", reply_markup=keyboard
        )
    except Exception:
        try:
            await query.message.reply_text(
                text, parse_mode="Markdown", reply_markup=keyboard
            )
        except Exception as e:
            print(f"safe_reply error: {e}")

# ── COMMANDS ──────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    await update.message.reply_text(
        f"🌍 *{t(lang, 'choose_lang')}*",
        parse_mode="Markdown",
        reply_markup=lang_keyboard()
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    await update.message.reply_text(
        "🤖 *Nexus OlympTrade Bot*\n\n"
        "📌 *Commands:*\n"
        "/start    - Start bot\n"
        "/signal   - Get signal\n"
        "/auto     - Auto signals\n"
        "/stopauto - 🛑 Stop auto signals\n"
        "/history  - Trade history\n"
        "/winrate  - Win rate stats\n"
        "/status   - Bot status\n"
        "/login    - Login OlympTrade\n"
        "/help     - This message",
        parse_mode="Markdown",
        reply_markup=home_keyboard(lang)
    )

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    auto = "🟢 ON" if is_auto_user(uid) else "🔴 OFF"
    try:
        from websocket_client import get_ws_status, live_prices
        ws = "🟢 Connected" if get_ws_status() else "🔴 Disconnected"
        prices = len(live_prices)
    except:
        ws = "🔴 Not started"
        prices = 0
    await update.message.reply_text(
        f"📡 *Bot Status*\n\n"
        f"✅ Bot: `Running`\n"
        f"🌐 WebSocket: {ws}\n"
        f"💹 Live Prices: `{prices} assets`\n"
        f"🧠 Engine: `BB + Stochastic`\n"
        f"📊 Assets: `{len(ALL_PAIRS)} OTC pairs`\n"
        f"🔄 Auto Signal: {auto}\n"
        f"🕐 Time: `{datetime.now().strftime('%H:%M:%S')}`\n"
        f"📅 Date: `{datetime.now().strftime('%d/%m/%Y')}`",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🛑 Stop Auto", callback_data="auto_stop")],
            [InlineKeyboardButton("🏠 Home",      callback_data="send_home")],
        ])
    )

async def signal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    await update.message.reply_text(
        f"⚡ *{t(lang, 'choose_mode')}*",
        parse_mode="Markdown",
        reply_markup=signal_mode_keyboard(lang)
    )

async def auto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid   = update.effective_user.id
    lang  = get_user_lang(uid)
    is_on = is_auto_user(uid)
    await update.message.reply_text(
        f"🤖 *Auto Signal*\n\n"
        f"Status: {'🟢 ON — Sending every 2 min' if is_on else '🔴 OFF'}\n\n"
        f"{'⚠️ Use /stopauto or tap STOP' if is_on else 'Tap Start Auto to begin'}",
        parse_mode="Markdown",
        reply_markup=make_auto_keyboard(is_on)
    )

async def stopauto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    unregister_auto_user(uid)
    await update.message.reply_text(
        "🛑 *Auto signals STOPPED!*\n\n"
        "You will no longer receive automatic signals.\n"
        "Use /auto to start again.",
        parse_mode="Markdown",
        reply_markup=main_menu_keyboard(lang)
    )

async def history_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    from trade_history import format_history
    await update.message.reply_text(
        format_history(uid),
        parse_mode="Markdown",
        reply_markup=history_keyboard(lang)
    )

async def winrate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    from trade_history import format_win_rate
    await update.message.reply_text(
        format_win_rate(uid),
        parse_mode="Markdown",
        reply_markup=home_keyboard(lang)
    )

# ── SEND SIGNAL ───────────────────────────────────────────────────────────────
async def send_signal(context, chat_id, asset, tf, duration, lang, uid):
    from trade_history import add_trade
    sig = get_signal(asset, tf)
    sig["asset"] = asset

    trade    = add_trade(uid, asset, sig["direction"], sig["price_str"], duration, sig["win_prob"])
    trade_id = trade["id"]
    text     = format_signal_text(sig, duration, lang)
    keyboard = make_signal_keyboard(asset, tf, duration, trade_id)

    try:
        chart_buf = draw_chart(sig)
        await context.bot.send_photo(
            chat_id=chat_id,
            photo=chart_buf,
            caption=text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
    except Exception as e:
        print(f"Chart error: {e}")
        await context.bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="Markdown",
            reply_markup=keyboard
        )

# ── BUTTON HANDLER ────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
    uid   = query.from_user.id
    lang  = get_user_lang(uid)

    try:
        # ── send_home: works on both text and photo messages ──────────────────
        if data == "send_home":
            await query.message.reply_text(
                f"🏠 *{t(lang,'main_menu')}*",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(lang)
            )

        elif data == "menu_home":
            await safe_reply(query,
                f"🏠 *{t(lang,'main_menu')}*",
                main_menu_keyboard(lang), lang
            )

        # ── Language ──────────────────────────────────────────────────────────
        elif data.startswith("lang_"):
            lang = data.replace("lang_", "")
            set_user_lang(uid, lang)
            await safe_reply(query,
                f"✅ {t(lang,'lang_set')}\n\n🤖 *{t(lang,'welcome')}*",
                main_menu_keyboard(lang), lang
            )

        elif data == "menu_signal":
            await safe_reply(query,
                f"⚡ *{t(lang,'choose_mode')}*",
                signal_mode_keyboard(lang), lang
            )

        elif data == "menu_lang":
            await safe_reply(query,
                f"🌍 *{t(lang,'choose_lang')}*",
                lang_keyboard(), lang
            )

        elif data == "menu_settings":
            await safe_reply(query,
                f"⚙️ *{t(lang,'settings')}*",
                settings_keyboard(lang), lang
            )

        elif data == "menu_account":
            await safe_reply(query,
                f"👤 *{t(lang,'my_account')}*",
                account_keyboard(lang), lang
            )

        elif data == "menu_status":
            auto = "🟢 ON" if is_auto_user(uid) else "🔴 OFF"
            try:
                from websocket_client import get_ws_status, live_prices
                ws     = "🟢 Live" if get_ws_status() else "🔴 Offline"
                prices = len(live_prices)
            except:
                ws = "🔴 Offline"; prices = 0
            await safe_reply(query,
                f"📡 *Status*\n\nBot: `Running`\n"
                f"WebSocket: {ws}\n"
                f"Live Prices: `{prices}`\n"
                f"Auto: {auto}\n"
                f"Time: `{datetime.now().strftime('%H:%M:%S')}`",
                InlineKeyboardMarkup([
                    [InlineKeyboardButton("🛑 Stop Auto", callback_data="auto_stop")],
                    [InlineKeyboardButton("🏠 Home",      callback_data="send_home")],
                ]), lang
            )

        elif data == "menu_help":
            await safe_reply(query,
                "📌 *Commands:*\n"
                "/signal   - Get signal\n"
                "/auto     - Auto signals\n"
                "/stopauto - Stop auto\n"
                "/history  - Trade history\n"
                "/winrate  - Win rate\n"
                "/login    - Login",
                home_keyboard(lang), lang
            )

        elif data == "menu_login":
            from login_handler import show_login
            await show_login(update, context)

        # ── Signal mode ───────────────────────────────────────────────────────
        elif data == "mode_immediate":
            set_user_session(uid, "mode", "immediate")
            await safe_reply(query,
                f"📊 *{t(lang,'choose_asset')}*",
                asset_category_keyboard(lang), lang
            )

        elif data == "mode_auto":
            set_user_session(uid, "mode", "auto")
            await safe_reply(query,
                f"📊 *{t(lang,'choose_asset')}*\n_For auto signals_",
                asset_category_keyboard(lang), lang
            )

        # ── Categories ────────────────────────────────────────────────────────
        elif data == "back_categories":
            await safe_reply(query,
                f"📊 *{t(lang,'choose_asset')}*",
                asset_category_keyboard(lang), lang
            )

        elif data.startswith("cat_"):
            cat_key = data.replace("cat_", "")
            cat = ASSETS[cat_key]
            await safe_reply(query,
                f"{cat['emoji']} *{t(lang,'choose_pair')}*",
                asset_list_keyboard(cat_key, lang), lang
            )

        # ── Asset ─────────────────────────────────────────────────────────────
        elif data.startswith("asset_"):
            key = data.replace("asset_", "")
            if key == "RANDOM":
                asset = random.choice(ALL_PAIRS)
            elif key == "BEST":
                asset = get_best_signal("1m")["asset"]
            else:
                asset = key
            set_user_session(uid, "asset", asset)
            await safe_reply(query,
                f"⏱ *{t(lang,'choose_tf')}*\n`{asset}`",
                timeframe_keyboard(asset, lang), lang
            )

        # ── Timeframe ─────────────────────────────────────────────────────────
        elif data.startswith("tf_"):
            parts = data[3:].split("|")
            asset = parts[0]
            tf    = parts[1] if len(parts) > 1 else "1m"
            set_user_session(uid, "tf", tf)
            await safe_reply(query,
                f"⏳ *{t(lang,'choose_dur')}*\n`{asset}` | `{tf}`",
                duration_keyboard(asset, tf, lang), lang
            )

        # ── Duration → Signal ─────────────────────────────────────────────────
        elif data.startswith("dur_"):
            parts    = data[4:].split("|")
            asset    = parts[0]
            tf       = parts[1] if len(parts) > 1 else "1m"
            duration = parts[2] if len(parts) > 2 else "1 min"
            mode     = get_user_session(uid, "mode", "immediate")

            await safe_reply(query,
                f"⏳ *{t(lang,'analysing')}*\n\n"
                f"Asset: `{asset}` | TF: `{tf}`\n"
                f"Analysing BB + Stochastic...",
                InlineKeyboardMarkup([]), lang
            )
            await asyncio.sleep(ANALYSIS_TIME)

            if mode == "auto":
                register_auto_user(uid, asset, tf, duration, lang)
                await query.message.reply_text(
                    f"✅ *Auto signals ON!*\n"
                    f"Asset: `{asset}` | TF: `{tf}`\n"
                    f"Every 2 minutes.\nUse /stopauto to stop.",
                    parse_mode="Markdown",
                    reply_markup=make_auto_keyboard(True)
                )

            await send_signal(context, uid, asset, tf, duration, lang, uid)

        # ── Trade confirm ─────────────────────────────────────────────────────
        elif data.startswith("trade_"):
            parts    = data[6:].split("|")
            asset    = parts[0]
            tf       = parts[1] if len(parts) > 1 else "1m"
            duration = parts[2] if len(parts) > 2 else "1 min"
            sig      = get_signal(asset, tf)
            await query.message.reply_text(
                f"⚠️ *{t(lang,'confirm_trade')}*\n\n"
                f"Asset: `{asset}`\n"
                f"Direction: `{sig['direction']}`\n"
                f"Duration: `{duration}`\n"
                f"Price: `{sig['price_str']}`",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup([
                    [
                        InlineKeyboardButton("✅ YES Trade",
                            callback_data=f"confirm_yes_{asset}|{tf}|{duration}|{sig['direction']}"),
                        InlineKeyboardButton("❌ NO Skip",
                            callback_data="confirm_no"),
                    ]
                ])
            )

        elif data.startswith("confirm_yes_"):
            parts     = data[12:].split("|")
            asset     = parts[0]
            direction = parts[3] if len(parts) > 3 else "BUY"
            await query.message.reply_text(
                f"✅ *Trade placed!*\n`{asset}` → `{direction}`\n_Auto trading coming soon!_",
                parse_mode="Markdown",
                reply_markup=home_keyboard(lang)
            )

        elif data == "confirm_no":
            await query.message.reply_text(
                "❌ Trade skipped.",
                reply_markup=home_keyboard(lang)
            )

        # ── Auto stop ─────────────────────────────────────────────────────────
        elif data == "auto_stop":
            unregister_auto_user(uid)
            await query.message.reply_text(
                "🛑 *Auto signals STOPPED!*\n\nUse /auto to start again.",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(lang)
            )

        elif data == "auto_toggle":
            if is_auto_user(uid):
                unregister_auto_user(uid)
                await query.message.reply_text(
                    "🛑 *Auto signals STOPPED!*",
                    parse_mode="Markdown",
                    reply_markup=make_auto_keyboard(False)
                )
            else:
                set_user_session(uid, "mode", "auto")
                await safe_reply(query,
                    f"📊 *Select asset for auto:*",
                    asset_category_keyboard(lang), lang
                )

        elif data == "auto_config":
            set_user_session(uid, "mode", "auto")
            await safe_reply(query,
                f"📊 *Select asset for auto signals:*",
                asset_category_keyboard(lang), lang
            )

        # ── Mark WIN/LOSS ─────────────────────────────────────────────────────
        elif data.startswith("mark_win_"):
            trade_id = int(data.replace("mark_win_", "") or 0)
            from trade_history import update_result
            update_result(uid, trade_id, "WIN", profit=0.85)
            await query.answer("✅ Marked as WIN!")

        elif data.startswith("mark_loss_"):
            trade_id = int(data.replace("mark_loss_", "") or 0)
            from trade_history import update_result
            update_result(uid, trade_id, "LOSS", profit=-1.0)
            await query.answer("❌ Marked as LOSS!")

        # ── History ───────────────────────────────────────────────────────────
        elif data in ["account_history", "history_refresh"]:
            from trade_history import format_history
            await safe_reply(query, format_history(uid), history_keyboard(lang), lang)

        elif data in ["account_winrate", "history_winrate"]:
            from trade_history import format_win_rate
            await safe_reply(query, format_win_rate(uid), history_keyboard(lang), lang)

        elif data == "history_clear":
            from trade_history import trade_records
            trade_records[uid] = []
            await safe_reply(query, "🗑 *History cleared!*", history_keyboard(lang), lang)

        elif data == "history_win":
            from trade_history import get_history, update_result, format_history
            trades = get_history(uid, 1)
            if trades:
                update_result(uid, trades[0]["id"], "WIN", profit=0.85)
            await safe_reply(query,
                "✅ Last trade marked WIN!\n\n" + format_history(uid, 5),
                history_keyboard(lang), lang
            )

        elif data == "history_loss":
            from trade_history import get_history, update_result, format_history
            trades = get_history(uid, 1)
            if trades:
                update_result(uid, trades[0]["id"], "LOSS", profit=-1.0)
            await safe_reply(query,
                "❌ Last trade marked LOSS!\n\n" + format_history(uid, 5),
                history_keyboard(lang), lang
            )

        # ── Account ───────────────────────────────────────────────────────────
        elif data == "account_balance":
            email  = get_user_session(uid, "email", None)
            logged = get_user_session(uid, "logged_in", False)
            if logged and email:
                await safe_reply(query,
                    f"💰 *Balance*\n\n📧 `{email}`\n💵 Demo: `$10,000`",
                    account_keyboard(lang), lang
                )
            else:
                await safe_reply(query,
                    "⚠️ Please /login first!",
                    account_keyboard(lang), lang
                )

        elif data == "account_logout":
            set_user_session(uid, "logged_in", False)
            set_user_session(uid, "email", None)
            await safe_reply(query, "🔓 Logged out.", home_keyboard(lang), lang)

        elif data in ["settings_notif", "settings_amount", "settings_duration"]:
            await safe_reply(query, "⚙️ *Setting coming soon!*", settings_keyboard(lang), lang)

        else:
            await query.answer("Coming soon!")

    except Exception as e:
        print(f"Button error [{data}]: {e}")
        try:
            await query.message.reply_text(
                "⚠️ Error. Use /menu to restart.",
                reply_markup=home_keyboard(lang)
            )
        except:
            pass
