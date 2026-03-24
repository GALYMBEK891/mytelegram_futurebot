# ============================================================
#  config.py — Bot & AI configuration
#  Secrets are loaded from .env via load_dotenv() in bot.py.
# ============================================================

import os

# ------ Telegram ------
# Loaded from .env: TELEGRAM_BOT_TOKEN
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# ------ Google Gemini ------
# Loaded from .env: GEMINI_API_KEY
GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")

# Model to use – gemini-2.0-flash is fast and capable
GEMINI_MODEL: str = "gemini-2.0-flash"

# ------ Bot behaviour ------
# Max tokens Gemini will generate per response
MAX_OUTPUT_TOKENS: int = 1024

# System instructions sent to Gemini before every conversation
SYSTEM_PROMPT: str = (
    "You are a helpful, friendly Telegram assistant. "
    "Answer clearly and concisely. "
    "Use Markdown formatting when it improves readability."
)
