import asyncio
import logging
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler, filters
)
from config import TELEGRAM_TOKEN
from handlers import (
    start, help_cmd, status_cmd,
    signal_cmd, auto_cmd, stopauto_cmd, button_handler
)
from login_handler import show_login, ask_email, ask_password, receive_text, submit_login
from signal_engine import start_engine
from auto_trader import auto_signal_loop

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)

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
    app.add_handler(CommandHandler("start",    start))
    app.add_handler(CommandHandler("help",     help_cmd))
    app.add_handler(CommandHandler("status",   status_cmd))
    app.add_handler(CommandHandler("signal",   signal_cmd))
    app.add_handler(CommandHandler("auto",     auto_cmd))
    app.add_handler(CommandHandler("stopauto", stopauto_cmd))
    app.add_handler(CommandHandler("login",    show_login))
    app.add_handler(CommandHandler("menu",     start))

    app.add_handler(CallbackQueryHandler(show_login,   pattern="^menu_login$"))
    app.add_handler(CallbackQueryHandler(ask_email,    pattern="^login_email$"))
    app.add_handler(CallbackQueryHandler(ask_password, pattern="^login_pass$"))
    app.add_handler(CallbackQueryHandler(submit_login, pattern="^login_submit$"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, receive_text))
    app.add_handler(CallbackQueryHandler(button_handler))

    print("Starting Nexus OlympTrade Bot...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    run()
