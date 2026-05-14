import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from config import TELEGRAM_TOKEN
from handlers import (
    start, help_cmd, status_cmd, signal_cmd,
    auto_cmd, stopauto_cmd, button_handler,
    history_cmd, winrate_cmd
)
from login_handler import show_login, ask_email, ask_password, receive_text, submit_login
from signal_engine import start_engine
from auto_trader import auto_signal_loop

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

async def handle_history_buttons(update, context):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    data  = query.data
    from trade_history import (
        format_history, format_win_rate,
        update_result, get_history, trade_records
    )
    from keyboards import history_keyboard, home_keyboard
    from signal_engine import get_user_lang
    lang = get_user_lang(uid)

    if data == "history_refresh" or data == "account_history":
        await query.edit_message_text(
            format_history(uid),
            parse_mode="Markdown",
            reply_markup=history_keyboard(lang)
        )

    elif data == "history_winrate" or data == "account_winrate":
        await query.edit_message_text(
            format_win_rate(uid),
            parse_mode="Markdown",
            reply_markup=history_keyboard(lang)
        )

    elif data == "history_clear":
        trade_records[uid] = []
        await query.edit_message_text(
            "🗑 *Trade history cleared!*",
            parse_mode="Markdown",
            reply_markup=history_keyboard(lang)
        )

    elif data == "history_win":
        trades = get_history(uid, 1)
        if trades:
            update_result(uid, trades[0]["id"], "WIN", profit=0.85)
        await query.edit_message_text(
            "✅ *Last trade marked as WIN!*\n\n" + format_history(uid, 5),
            parse_mode="Markdown",
            reply_markup=history_keyboard(lang)
        )

    elif data == "history_loss":
        trades = get_history(uid, 1)
        if trades:
            update_result(uid, trades[0]["id"], "LOSS", profit=-1.0)
        await query.edit_message_text(
            "❌ *Last trade marked as LOSS!*\n\n" + format_history(uid, 5),
            parse_mode="Markdown",
            reply_markup=history_keyboard(lang)
        )

    elif data.startswith("mark_win_"):
        trade_id = int(data.replace("mark_win_", ""))
        update_result(uid, trade_id, "WIN", profit=0.85)
        await query.answer("✅ Marked as WIN!")

    elif data.startswith("mark_loss_"):
        trade_id = int(data.replace("mark_loss_", ""))
        update_result(uid, trade_id, "LOSS", profit=-1.0)
        await query.answer("❌ Marked as LOSS!")

async def post_init(app):
    start_engine()
    asyncio.create_task(auto_signal_loop(app))
    print("Nexus OlympTrade Bot fully started!")

def run():
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_cmd))
    app.add_handler(CommandHandler("status",   status_cmd))
    app.add_handler(CommandHandler("signal",   signal_cmd))
    app.add_handler(CommandHandler("auto",     auto_cmd))
    app.add_handler(CommandHandler("stopauto", stopauto_cmd))
    app.add_handler(CommandHandler("login",    show_login))
    app.add_handler(CommandHandler("history",  history_cmd))
    app.add_handler(CommandHandler("winrate",  winrate_cmd))
    app.add_handler(CommandHandler("menu",     start))

    # Login
    app.add_handler(CallbackQueryHandler(show_login,   pattern="^menu_login$"))
    app.add_handler(CallbackQueryHandler(ask_email,    pattern="^login_email$"))
    app.add_handler(CallbackQueryHandler(ask_password, pattern="^login_pass$"))
    app.add_handler(CallbackQueryHandler(submit_login, pattern="^login_submit$"))

    # History & Win rate
    app.add_handler(CallbackQueryHandler(
        handle_history_buttons,
        pattern="^(history_|account_history|account_winrate|mark_win_|mark_loss_)"
    ))

    # Text input
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))

    # All other buttons
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Starting Nexus OlympTrade Bot...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    run()
