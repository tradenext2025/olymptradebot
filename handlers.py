# ─── BOT HANDLERS (FIXED) ─────────────────────────────────────────────────────
import asyncio
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from languages import t
from keyboards import (
    lang_keyboard, main_menu_keyboard, signal_mode_keyboard,
    asset_category_keyboard, asset_list_keyboard, timeframe_keyboard,
    duration_keyboard, signal_result_keyboard, trade_confirm_keyboard,
    auto_signal_keyboard, settings_keyboard, account_keyboard, home_keyboard
)
from signal_engine import (
    get_signal, get_best_signal, format_signal_text,
    set_user_lang, get_user_lang, set_user_session, get_user_session,
    register_auto_user, unregister_auto_user, is_auto_user
)
from chart import draw_chart
from config import ASSETS, ALL_PAIRS, ANALYSIS_TIME
import random

# ── START ─────────────────────────────────────────────────────────────────────
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
        "/start  - Start bot\n"
        "/signal - Get signal\n"
        "/auto   - Auto signals\n"
        "/stopauto - Stop auto signals\n"
        "/status - Bot status\n"
        "/login  - Login OlympTrade\n"
        "/help   - This message",
        parse_mode="Markdown",
        reply_markup=home_keyboard(lang)
    )

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    auto = "🟢 ON" if is_auto_user(uid) else "🔴 OFF"
    await update.message.reply_text(
        f"📡 *Bot Status*\n\n"
        f"✅ Bot: `Running`\n"
        f"🧠 Engine: `BB + Stochastic`\n"
        f"📊 Assets: `{len(ALL_PAIRS)} OTC pairs`\n"
        f"⏰ Timeframes: `5s, 10s, 30s, 1m, 5m`\n"
        f"🔄 Auto Signal: {auto}\n"
        f"🕐 Time: `{datetime.now().strftime('%H:%M:%S')}`\n"
        f"📅 Date: `{datetime.now().strftime('%d/%m/%Y')}`",
        parse_mode="Markdown",
        reply_markup=home_keyboard(lang)
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
        f"Status: {'🟢 ON - Sending every 2 min' if is_on else '🔴 OFF'}\n\n"
        f"{'Use /stopauto to stop' if is_on else 'Tap Start Auto to begin'}",
        parse_mode="Markdown",
        reply_markup=auto_signal_keyboard(is_on, lang)
    )

async def stopauto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    if is_auto_user(uid):
        unregister_auto_user(uid)
        await update.message.reply_text(
            "🔴 *Auto signals stopped!*\n\nYou will no longer receive automatic signals.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang)
        )
    else:
        await update.message.reply_text(
            "ℹ️ Auto signals are already OFF.",
            parse_mode="Markdown",
            reply_markup=main_menu_keyboard(lang)
        )

# ── BUTTON HANDLER ────────────────────────────────────────────────────────────
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data  = query.data
    uid   = query.from_user.id
    lang  = get_user_lang(uid)

    try:
        # ── Language ──────────────────────────────────────────────────────────
        if data.startswith("lang_"):
            lang = data.replace("lang_", "")
            set_user_lang(uid, lang)
            await query.edit_message_text(
                f"✅ {t(lang, 'lang_set')}\n\n"
                f"🤖 *{t(lang, 'welcome')}*\n\n"
                f"📌 {t(lang, 'main_menu')}:",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(lang)
            )

        # ── Home ──────────────────────────────────────────────────────────────
        elif data == "menu_home":
            await query.edit_message_text(
                f"🏠 *{t(lang, 'main_menu')}*",
                parse_mode="Markdown",
                reply_markup=main_menu_keyboard(lang)
            )

        # ── Menu items ────────────────────────────────────────────────────────
        elif data == "menu_signal":
            await query.edit_message_text(
                f"⚡ *{t(lang, 'choose_mode')}*",
                parse_mode="Markdown",
                reply_markup=signal_mode_keyboard(lang)
            )

        elif data == "menu_lang":
            await query.edit_message_text(
                f"🌍 *{t(lang, 'choose_lang')}*",
                parse_mode="Markdown",
                reply_markup=lang_keyboard()
            )

        elif data == "menu_settings":
            await query.edit_message_text(
                f"⚙️ *{t(lang, 'settings')}*",
                parse_mode="Markdown",
                reply_markup=settings_keyboard(lang)
            )

        elif data == "menu_account":
            await query.edit_message_text(
                f"👤 *{t(lang, 'my_account')}*",
                parse_mode="Markdown",
                reply_markup=account_keyboard(lang)
            )

        elif data == "menu_status":
            auto = "🟢 ON" if is_auto_user(uid) else "🔴 OFF"
            await query.edit_message_text(
                f"📡 *{t(lang,'status')}*\n\n"
                f"✅ Bot: `Running`\n"
                f"🧠 Engine: `BB + Stochastic`\n"
                f"📊 Assets: `{len(ALL_PAIRS)} OTC pairs`\n"
                f"🔄 Auto Signal: {auto}\n"
                f"🕐 Time: `{datetime.now().strftime('%H:%M:%S')}`",
                parse_mode="Markdown",
                reply_markup=home_keyboard(lang)
            )

        elif data == "menu_help":
            await query.edit_message_text(
                "📌 *Commands:*\n"
                "/start    - Start bot\n"
                "/signal   - Get signal\n"
                "/auto     - Auto signals\n"
                "/stopauto - Stop auto signals\n"
                "/status   - Bot status\n"
                "/login    - Login OlympTrade\n\n"
                "📊 *Indicators:*\n"
                "• Bollinger Bands (20,2)\n"
                "• Stochastic (14,3)\n"
                "• 24/7 Analysis all timeframes",
                parse_mode="Markdown",
                reply_markup=home_keyboard(lang)
            )

        elif data == "menu_login":
            from login_handler import show_login
            await show_login(update, context)

        # ── Signal mode ───────────────────────────────────────────────────────
        elif data == "mode_immediate":
            set_user_session(uid, "mode", "immediate")
            await query.edit_message_text(
                f"📊 *{t(lang, 'choose_asset')}*",
                parse_mode="Markdown",
                reply_markup=asset_category_keyboard(lang)
            )

        elif data == "mode_auto":
            set_user_session(uid, "mode", "auto")
            await query.edit_message_text(
                f"📊 *{t(lang, 'choose_asset')}*\n_For auto signals_",
                parse_mode="Markdown",
                reply_markup=asset_category_keyboard(lang)
            )

        # ── Categories ────────────────────────────────────────────────────────
        elif data == "back_categories":
            await query.edit_message_text(
                f"📊 *{t(lang, 'choose_asset')}*",
                parse_mode="Markdown",
                reply_markup=asset_category_keyboard(lang)
            )

        elif data.startswith("cat_"):
            cat_key = data.replace("cat_", "")
            cat = ASSETS[cat_key]
            await query.edit_message_text(
                f"{cat['emoji']} *{t(lang,'choose_pair')}*\n_{cat['label']}_",
                parse_mode="Markdown",
                reply_markup=asset_list_keyboard(cat_key, lang)
            )

        # ── Asset selected ────────────────────────────────────────────────────
        elif data.startswith("asset_"):
            key = data.replace("asset_", "")
            if key == "RANDOM":
                asset = random.choice(ALL_PAIRS)
            elif key == "BEST":
                sig   = get_best_signal("1m")
                asset = sig["asset"]
            else:
                asset = key
            set_user_session(uid, "asset", asset)
            await query.edit_message_text(
                f"⏱ *{t(lang,'choose_tf')}*\n`{asset}`",
                parse_mode="Markdown",
                reply_markup=timeframe_keyboard(asset, lang)
            )

        # ── Timeframe selected ────────────────────────────────────────────────
        elif data.startswith("tf_"):
            parts = data[3:].split("|")
            asset = parts[0]
            tf    = parts[1] if len(parts) > 1 else "1m"
            set_user_session(uid, "tf", tf)
            await query.edit_message_text(
                f"⏳ *{t(lang,'choose_dur')}*\n`{asset}` | `{tf}`",
                parse_mode="Markdown",
                reply_markup=duration_keyboard(asset, tf, lang)
            )

        # ── Duration → Generate signal ────────────────────────────────────────
        elif data.startswith("dur_"):
            parts    = data[4:].split("|")
            asset    = parts[0]
            tf       = parts[1] if len(parts) > 1 else "1m"
            duration = parts[2] if len(parts) > 2 else "1 min"
            mode     = get_user_session(uid, "mode", "immediate")

            await query.edit_message_text(
                f"⏳ *{t(lang, 'analysing')}*\n\n"
                f"Asset: `{asset}`\n"
                f"Timeframe: `{tf}`\n"
                f"Indicators: `BB + Stochastic`",
                parse_mode="Markdown"
            )

            await asyncio.sleep(ANALYSIS_TIME)

            sig = get_signal(asset, tf)
            sig["asset"] = asset

            if mode == "auto":
                register_auto_user(uid, asset, tf, duration, lang)
                await query.message.reply_text(
                    f"✅ *{t(lang,'auto_on')}*\n"
                    f"Asset: `{asset}` | TF: `{tf}`\n"
                    f"Use /stopauto to stop anytime.",
                    parse_mode="Markdown",
                    reply_markup=auto_signal_keyboard(True, lang)
                )

            try:
                chart_buf = draw_chart(sig)
                caption   = format_signal_text(sig, duration, lang)
                await query.message.reply_photo(
                    photo=chart_buf,
                    caption=caption,
                    parse_mode="Markdown",
                    reply_markup=signal_result_keyboard(asset, tf, duration, lang)
                )
                await query.delete_message()
            except Exception as e:
                text = format_signal_text(sig, duration, lang)
                await query.edit_message_text(
                    text,
                    parse_mode="Markdown",
                    reply_markup=signal_result_keyboard(asset, tf, duration, lang)
                )

        # ── Trade confirm ─────────────────────────────────────────────────────
        elif data.startswith("trade_"):
            parts     = data[6:].split("|")
            asset     = parts[0]
            tf        = parts[1] if len(parts) > 1 else "1m"
            duration  = parts[2] if len(parts) > 2 else "1 min"
            sig       = get_signal(asset, tf)
            direction = sig["direction"]
            await query.edit_message_text(
                f"⚠️ *{t(lang,'confirm_trade')}*\n\n"
                f"Asset: `{asset}`\n"
                f"Direction: `{direction}`\n"
                f"Duration: `{duration}`\n"
                f"Price: `{sig['price_str']}`",
                parse_mode="Markdown",
                reply_markup=trade_confirm_keyboard(asset, tf, duration, direction, lang)
            )

        elif data.startswith("confirm_yes_"):
            parts     = data[12:].split("|")
            asset     = parts[0]
            direction = parts[3] if len(parts) > 3 else "BUY"
            await query.edit_message_text(
                f"✅ *{t(lang,'trade_placed')}*\n\n"
                f"Asset: `{asset}`\n"
                f"Direction: `{direction}`\n"
                f"_Auto trading coming soon!_",
                parse_mode="Markdown",
                reply_markup=home_keyboard(lang)
            )

        elif data == "confirm_no":
            await query.edit_message_text(
                f"❌ *{t(lang,'trade_skipped')}*",
                parse_mode="Markdown",
                reply_markup=home_keyboard(lang)
            )

        # ── Auto toggle ───────────────────────────────────────────────────────
        elif data == "auto_toggle":
            if is_auto_user(uid):
                unregister_auto_user(uid)
                await query.edit_message_text(
                    f"🔴 *{t(lang,'auto_off')}*\n\nAuto signals stopped.",
                    parse_mode="Markdown",
                    reply_markup=main_menu_keyboard(lang)
                )
            else:
                set_user_session(uid, "mode", "auto")
                await query.edit_message_text(
                    f"📊 *Select asset for auto signals:*",
                    parse_mode="Markdown",
                    reply_markup=asset_category_keyboard(lang)
                )

        elif data == "auto_config":
            set_user_session(uid, "mode", "auto")
            await query.edit_message_text(
                f"📊 *{t(lang,'choose_asset')}*\n_For auto signals_",
                parse_mode="Markdown",
                reply_markup=asset_category_keyboard(lang)
            )

        # ── Account ───────────────────────────────────────────────────────────
        elif data == "account_balance":
            from signal_engine import get_user_session as gs
            email = gs(uid, "email", None)
            logged = gs(uid, "logged_in", False)
            if logged and email:
                await query.edit_message_text(
                    f"💰 *Account Balance*\n\n"
                    f"📧 Email: `{email}`\n"
                    f"💵 Demo: `$10,000.00`\n"
                    f"💵 Real: `Connect to see`\n"
                    f"_Live balance coming soon!_",
                    parse_mode="Markdown",
                    reply_markup=account_keyboard(lang)
                )
            else:
                await query.edit_message_text(
                    "⚠️ *Please login first!*\n\nUse /login to connect.",
                    parse_mode="Markdown",
                    reply_markup=account_keyboard(lang)
                )

        elif data == "account_history":
            await query.edit_message_text(
                "📊 *Trade History*\n\n_Coming soon!_",
                parse_mode="Markdown",
                reply_markup=account_keyboard(lang)
            )

        elif data == "account_logout":
            set_user_session(uid, "logged_in", False)
            set_user_session(uid, "email", None)
            await query.edit_message_text(
                "🔓 *Logged out successfully.*",
                parse_mode="Markdown",
                reply_markup=home_keyboard(lang)
            )

        elif data == "settings_notif":
            await query.edit_message_text(
                "🔔 *Notifications*\n\n✅ Signals: ON\n✅ Auto: ON\n_More settings coming soon!_",
                parse_mode="Markdown",
                reply_markup=settings_keyboard(lang)
            )

        elif data == "settings_amount":
            await query.edit_message_text(
                "💰 *Default Trade Amount*\n\n_Coming soon!_",
                parse_mode="Markdown",
                reply_markup=settings_keyboard(lang)
            )

        elif data == "settings_duration":
            await query.edit_message_text(
                "⏱ *Default Duration*\n\n_Coming soon!_",
                parse_mode="Markdown",
                reply_markup=settings_keyboard(lang)
            )

    except Exception as e:
        print(f"Button error: {e}")
        try:
            await query.edit_message_text(
                "⚠️ Something went wrong. Please try again.",
                reply_markup=home_keyboard(lang)
            )
        except:
            pass
