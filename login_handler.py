# ─── LOGIN HANDLER ─────────────────────────────────────────────────────────────
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes, ConversationHandler,
    MessageHandler, CommandHandler, filters
)
from signal_engine import set_user_lang, get_user_lang, set_user_session, get_user_session
from languages import t
from keyboards import home_keyboard, main_menu_keyboard

# States
WAITING_EMAIL    = 10
WAITING_PASSWORD = 11

# Store credentials temporarily
user_credentials = {}

# ── LOGIN KEYBOARD ─────────────────────────────────────────────────────────────
def login_keyboard(lang="en"):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("📧 Enter Email",    callback_data="login_email")],
        [InlineKeyboardButton("🔑 Enter Password", callback_data="login_pass")],
        [InlineKeyboardButton("✅ Login Now",       callback_data="login_submit")],
        [InlineKeyboardButton("❌ Cancel",          callback_data="menu_home")],
    ])

def login_status_keyboard(has_email, has_pass, lang="en"):
    email_btn  = "✅ Email Set"    if has_email else "📧 Enter Email"
    pass_btn   = "✅ Password Set" if has_pass  else "🔑 Enter Password"
    can_login  = has_email and has_pass
    buttons = [
        [InlineKeyboardButton(email_btn,  callback_data="login_email")],
        [InlineKeyboardButton(pass_btn,   callback_data="login_pass")],
    ]
    if can_login:
        buttons.append([InlineKeyboardButton("🚀 Login Now!", callback_data="login_submit")])
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="menu_home")])
    return InlineKeyboardMarkup(buttons)

# ── SHOW LOGIN MENU ────────────────────────────────────────────────────────────
async def show_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid  = update.effective_user.id
    lang = get_user_lang(uid)
    creds = user_credentials.get(uid, {})
    has_email = bool(creds.get("email"))
    has_pass  = bool(creds.get("password"))

    msg = (
        f"🔐 *Login to OlympTrade*\n\n"
        f"📧 Email: {'`✅ Set`' if has_email else '`Not set`'}\n"
        f"🔑 Password: {'`✅ Set`' if has_pass else '`Not set`'}\n\n"
        f"_Your credentials are used only to trade on your behalf._"
    )

    if hasattr(update, 'callback_query') and update.callback_query:
        await update.callback_query.edit_message_text(
            msg,
            parse_mode="Markdown",
            reply_markup=login_status_keyboard(has_email, has_pass, lang)
        )
    else:
        await update.message.reply_text(
            msg,
            parse_mode="Markdown",
            reply_markup=login_status_keyboard(has_email, has_pass, lang)
        )

# ── ASK EMAIL ─────────────────────────────────────────────────────────────────
async def ask_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_user_lang(uid)
    context.user_data["waiting"] = "email"
    await query.edit_message_text(
        "📧 *Enter your OlympTrade Email:*\n\n"
        "_Type your email address and send it_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="menu_login")]
        ])
    )

# ── ASK PASSWORD ──────────────────────────────────────────────────────────────
async def ask_password(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_user_lang(uid)
    context.user_data["waiting"] = "password"
    await query.edit_message_text(
        "🔑 *Enter your OlympTrade Password:*\n\n"
        "_Type your password and send it_\n"
        "⚠️ _Message will be deleted after saving_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("❌ Cancel", callback_data="menu_login")]
        ])
    )

# ── RECEIVE TEXT (email or password) ──────────────────────────────────────────
async def receive_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid     = update.effective_user.id
    lang    = get_user_lang(uid)
    text    = update.message.text.strip()
    waiting = context.user_data.get("waiting")

    if not waiting:
        return

    if uid not in user_credentials:
        user_credentials[uid] = {}

    if waiting == "email":
        user_credentials[uid]["email"] = text
        context.user_data["waiting"] = None
        # Delete user message for privacy
        try: await update.message.delete()
        except: pass
        creds    = user_credentials.get(uid, {})
        has_email = True
        has_pass  = bool(creds.get("password"))
        await update.message.reply_text(
            f"✅ *Email saved!*\n\n"
            f"📧 Email: `✅ Set`\n"
            f"🔑 Password: {'`✅ Set`' if has_pass else '`Not set`'}\n\n"
            f"{'Now tap Login Now!' if has_pass else 'Now enter your password.'}",
            parse_mode="Markdown",
            reply_markup=login_status_keyboard(has_email, has_pass, lang)
        )

    elif waiting == "password":
        user_credentials[uid]["password"] = text
        context.user_data["waiting"] = None
        # Delete user message for privacy
        try: await update.message.delete()
        except: pass
        creds    = user_credentials.get(uid, {})
        has_email = bool(creds.get("email"))
        has_pass  = True
        await update.message.reply_text(
            f"✅ *Password saved!*\n\n"
            f"📧 Email: {'`✅ Set`' if has_email else '`Not set`'}\n"
            f"🔑 Password: `✅ Set`\n\n"
            f"{'Now tap Login Now!' if has_email else 'Now enter your email.'}",
            parse_mode="Markdown",
            reply_markup=login_status_keyboard(has_email, has_pass, lang)
        )

# ── SUBMIT LOGIN ──────────────────────────────────────────────────────────────
async def submit_login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    uid   = query.from_user.id
    lang  = get_user_lang(uid)
    creds = user_credentials.get(uid, {})

    if not creds.get("email") or not creds.get("password"):
        await query.edit_message_text(
            "⚠️ *Please enter both email and password first!*",
            parse_mode="Markdown",
            reply_markup=login_status_keyboard(
                bool(creds.get("email")),
                bool(creds.get("password")),
                lang
            )
        )
        return

    # Show logging in
    await query.edit_message_text(
        "⏳ *Logging in to OlympTrade...*",
        parse_mode="Markdown"
    )

    # Save session
    set_user_session(uid, "email",    creds["email"])
    set_user_session(uid, "logged_in", True)

    await query.edit_message_text(
        f"✅ *{t(lang,'login_success')}*\n\n"
        f"📧 Account: `{creds['email']}`\n"
        f"🔐 Status: `Logged In`\n\n"
        f"_You can now use auto-trading features!_",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📊 Get Signal", callback_data="menu_signal")],
            [InlineKeyboardButton("🏠 Home",       callback_data="menu_home")],
        ])
    )
