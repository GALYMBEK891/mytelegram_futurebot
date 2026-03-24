#!/usr/bin/env python3
"""
bot.py — Professional Telegram bot powered by Gemini 2.0 Flash
Run: python bot.py
"""

import logging
import textwrap

from dotenv import load_dotenv

# Load .env BEFORE importing config so os.getenv() calls resolve correctly
load_dotenv()

import telebot
import google.generativeai as genai
from telebot.types import Message

import config


# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Gemini setup ─────────────────────────────────────────────────────────────
genai.configure(api_key=config.GEMINI_API_KEY)

gemini_model = genai.GenerativeModel(
    model_name=config.GEMINI_MODEL,
    system_instruction=config.SYSTEM_PROMPT,
    generation_config=genai.GenerationConfig(
        max_output_tokens=config.MAX_OUTPUT_TOKENS,
    ),
)

# Per-user conversation history  {user_id: ChatSession}
chat_sessions: dict[int, genai.ChatSession] = {}


def get_or_create_session(user_id: int) -> genai.ChatSession:
    """Return an existing chat session or create a fresh one."""
    if user_id not in chat_sessions:
        chat_sessions[user_id] = gemini_model.start_chat(history=[])
        logger.info("New chat session created for user %d", user_id)
    return chat_sessions[user_id]


def ask_gemini(user_id: int, text: str) -> str:
    """Send a message to Gemini and return the reply text."""
    session = get_or_create_session(user_id)
    try:
        response = session.send_message(text)
        return response.text
    except Exception as exc:
        logger.error("Gemini error for user %d: %s", user_id, exc)
        return "⚠️ Sorry, I couldn't reach the AI right now. Please try again."


# ── Bot setup ─────────────────────────────────────────────────────────────────
bot = telebot.TeleBot(config.TELEGRAM_BOT_TOKEN, parse_mode="Markdown")


# ── Helper ────────────────────────────────────────────────────────────────────
def full_name(message: Message) -> str:
    """Return the user's full name (or username as fallback)."""
    first = message.from_user.first_name or ""
    last = message.from_user.last_name or ""
    name = f"{first} {last}".strip()
    return name or message.from_user.username or "friend"


# ── Commands ──────────────────────────────────────────────────────────────────
@bot.message_handler(commands=["start"])
def handle_start(message: Message) -> None:
    """Greet the user by name."""
    name = full_name(message)
    greeting = textwrap.dedent(f"""
        👋 *Hello, {name}!*

        Welcome to your AI-powered assistant, running on *Gemini 2.0 Flash* ⚡

        Just send me any message and I'll do my best to help you.
        Type /help to see what I can do.
    """).strip()
    bot.reply_to(message, greeting)
    logger.info("/start from %s (id=%d)", name, message.from_user.id)


@bot.message_handler(commands=["help"])
def handle_help(message: Message) -> None:
    """Show available commands."""
    help_text = textwrap.dedent("""
        🤖 *Available Commands*

        /start — Restart & get a greeting
        /help  — Show this help message
        /reset — Clear your conversation history
        /about — About this bot

        💬 *Just chat!*
        Send any text message and I'll reply using *Gemini 2.0 Flash*.
    """).strip()
    bot.reply_to(message, help_text)


@bot.message_handler(commands=["reset"])
def handle_reset(message: Message) -> None:
    """Clear the user's chat history with Gemini."""
    user_id = message.from_user.id
    chat_sessions.pop(user_id, None)
    bot.reply_to(message, "🔄 Conversation history cleared. Let's start fresh!")
    logger.info("/reset from user id=%d", user_id)


@bot.message_handler(commands=["about"])
def handle_about(message: Message) -> None:
    """Show information about the bot."""
    about_text = textwrap.dedent(f"""
        ℹ️ *About This Bot*

        Built with:
        • 🐍 Python & pyTelegramBotAPI
        • ✨ Google Gemini 2.0 Flash

        Model: `{config.GEMINI_MODEL}`
        Max tokens per reply: `{config.MAX_OUTPUT_TOKENS}`
    """).strip()
    bot.reply_to(message, about_text)


# ── Free-text handler ─────────────────────────────────────────────────────────
@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_text(message: Message) -> None:
    """Pass any text message through Gemini and reply."""
    user_id = message.from_user.id
    user_text = message.text.strip()

    if not user_text:
        bot.reply_to(message, "Please send me a text message.")
        return

    # Show typing indicator while Gemini processes
    bot.send_chat_action(message.chat.id, "typing")

    reply = ask_gemini(user_id, user_text)
    bot.reply_to(message, reply)

    logger.info(
        "User %d | prompt=%d chars | reply=%d chars",
        user_id, len(user_text), len(reply),
    )


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Bot starting — model: %s", config.GEMINI_MODEL)
    print("🤖 Bot is running. Press Ctrl+C to stop.")
    bot.infinity_polling(timeout=30, long_polling_timeout=20)
