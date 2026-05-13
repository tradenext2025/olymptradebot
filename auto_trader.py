# ─── AUTO TRADER (Background 24/7 Signal Sender) ──────────────────────────────
import asyncio
import time
from datetime import datetime
from signal_engine import (
    get_signal, get_due_auto_users, mark_sent,
    format_signal_text, get_user_lang
)
from chart import draw_chart

# ── AUTO SIGNAL LOOP ──────────────────────────────────────────────────────────
async def auto_signal_loop(app):
    print("Auto trader started - sending signals every 2 minutes")
    while True:
        try:
            due_users = get_due_auto_users()
            for uid, data in due_users:
                try:
                    asset    = data["asset"]
                    tf       = data["timeframe"]
                    duration = data["duration"]
                    lang     = data["lang"]

                    # Get fresh signal
                    sig = get_signal(asset, tf)
                    sig["asset"] = asset

                    # Format text
                    text = format_signal_text(sig, duration, lang)

                    # Draw chart
                    try:
                        chart_buf = draw_chart(sig)
                        await app.bot.send_photo(
                            chat_id=uid,
                            photo=chart_buf,
                            caption=text,
                            parse_mode="Markdown"
                        )
                    except Exception:
                        # Fallback to text only
                        await app.bot.send_message(
                            chat_id=uid,
                            text=text,
                            parse_mode="Markdown"
                        )

                    mark_sent(uid)
                    print(f"Auto signal sent to {uid} - {asset} {tf} {sig['direction']}")

                except Exception as e:
                    print(f"Error sending auto signal to {uid}: {e}")

        except Exception as e:
            print(f"Auto trader loop error: {e}")

        await asyncio.sleep(10)  # check every 10 seconds
