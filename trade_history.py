# ─── TRADE HISTORY & WIN RATE ─────────────────────────────────────────────────
from datetime import datetime

# Storage: { user_id: [ {trade_dict}, ... ] }
trade_records = {}

# ── ADD TRADE ─────────────────────────────────────────────────────────────────
def add_trade(user_id, asset, direction, entry_price, duration, win_prob):
    if user_id not in trade_records:
        trade_records[user_id] = []
    trade = {
        "id":          len(trade_records[user_id]) + 1,
        "asset":       asset,
        "direction":   direction,
        "entry_price": entry_price,
        "duration":    duration,
        "win_prob":    win_prob,
        "result":      None,   # "WIN" / "LOSS" / "PENDING"
        "profit":      0.0,
        "time":        datetime.now().strftime("%H:%M:%S"),
        "date":        datetime.now().strftime("%d/%m/%Y"),
        "timestamp":   datetime.now().isoformat(),
    }
    trade_records[user_id].append(trade)
    return trade

# ── UPDATE RESULT ─────────────────────────────────────────────────────────────
def update_result(user_id, trade_id, result, profit=0.0):
    if user_id not in trade_records:
        return
    for trade in trade_records[user_id]:
        if trade["id"] == trade_id:
            trade["result"] = result
            trade["profit"] = profit
            break

# ── GET STATS ─────────────────────────────────────────────────────────────────
def get_stats(user_id):
    trades  = trade_records.get(user_id, [])
    total   = len(trades)
    decided = [t for t in trades if t["result"] in ["WIN", "LOSS"]]
    wins    = [t for t in decided if t["result"] == "WIN"]
    losses  = [t for t in decided if t["result"] == "LOSS"]
    pending = [t for t in trades if t["result"] == "PENDING" or t["result"] is None]

    win_rate = round(len(wins) / len(decided) * 100, 1) if decided else 0.0
    total_profit = round(sum(t["profit"] for t in decided), 2)

    return {
        "total":        total,
        "wins":         len(wins),
        "losses":       len(losses),
        "pending":      len(pending),
        "win_rate":     win_rate,
        "total_profit": total_profit,
        "decided":      len(decided),
    }

# ── GET HISTORY ───────────────────────────────────────────────────────────────
def get_history(user_id, limit=10):
    trades = trade_records.get(user_id, [])
    return list(reversed(trades[-limit:]))

# ── FORMAT HISTORY ────────────────────────────────────────────────────────────
def format_history(user_id, limit=10):
    trades = get_history(user_id, limit)
    stats  = get_stats(user_id)

    if not trades:
        return (
            "📊 *Trade History*\n\n"
            "No trades yet!\n"
            "Use /signal to get your first signal."
        )

    # Win rate bar
    rate  = stats["win_rate"]
    bars  = int(rate / 10)
    bar   = "🟩" * bars + "🟥" * (10 - bars)

    lines = [
        f"📊 *Trade History*",
        f"━━━━━━━━━━━━━━━━━━━━━",
        f"📈 Win Rate: `{rate}%`",
        f"{bar}",
        f"✅ Wins: `{stats['wins']}`  ❌ Losses: `{stats['losses']}`  ⏳ Pending: `{stats['pending']}`",
        f"💰 Total Profit: `${stats['total_profit']}`",
        f"📋 Total Trades: `{stats['total']}`",
        f"━━━━━━━━━━━━━━━━━━━━━",
        f"*Last {min(limit, len(trades))} Trades:*",
        f"",
    ]

    for t in trades:
        if t["result"] == "WIN":
            emoji = "✅"
        elif t["result"] == "LOSS":
            emoji = "❌"
        else:
            emoji = "⏳"

        direction_emoji = "📈" if t["direction"] == "BUY" else "📉"
        profit_str = f"+${t['profit']}" if t["profit"] > 0 else f"-${abs(t['profit'])}" if t["profit"] < 0 else ""

        lines.append(
            f"{emoji} {direction_emoji} `{t['asset']}`\n"
            f"   Price: `{t['entry_price']}` | {t['duration']}\n"
            f"   {t['date']} {t['time']} {profit_str}"
        )
        lines.append("")

    return "\n".join(lines)

# ── FORMAT WIN RATE ───────────────────────────────────────────────────────────
def format_win_rate(user_id):
    stats = get_stats(user_id)
    rate  = stats["win_rate"]

    if rate >= 80:   grade = "🏆 EXCELLENT"
    elif rate >= 70: grade = "✅ GOOD"
    elif rate >= 60: grade = "⚡ AVERAGE"
    elif rate >= 50: grade = "⚠️ BELOW AVERAGE"
    else:            grade = "❌ NEEDS IMPROVEMENT"

    bars = int(rate / 10)
    bar  = "🟩" * bars + "🟥" * (10 - bars)

    return (
        f"📊 *Win Rate Analysis*\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"🎯 Win Rate: `{rate}%`\n"
        f"{bar}\n"
        f"Grade: {grade}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"✅ Wins:    `{stats['wins']}`\n"
        f"❌ Losses:  `{stats['losses']}`\n"
        f"⏳ Pending: `{stats['pending']}`\n"
        f"📋 Total:   `{stats['total']}`\n"
        f"💰 Profit:  `${stats['total_profit']}`\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"_Track your trades to improve accuracy!_"
    )
