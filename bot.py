import os
import logging
from typing import Optional
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from deepl import Translator
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Initialize DeepL translator
DEEPL_API_KEY = os.getenv('DEEPL_API_KEY')
if not DEEPL_API_KEY:
    raise ValueError("DEEPL_API_KEY not found in environment variables")

translator = Translator(DEEPL_API_KEY)

# Test the translator
try:
    translator.translate_text("test", target_lang="EN-GB")
    logger.info("DeepL translator initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize translator: {e}")
    raise

async def translate_text(text: str) -> Optional[str]:
    """Translate text between English and Portuguese"""
    try:
        # Clean the text
        text = ' '.join(text.strip().split())
        if not text:
            return None

        # Try both translations without source language
        try:
            # Let DeepL detect and translate to Portuguese
            result = translator.translate_text(text, target_lang='PT-PT')
            if result.text.lower() != text.lower():
                return f"🇵🇹 {result.text}"
        except Exception as e:
            logger.error(f"->PT failed: {e}")

        try:
            # Let DeepL detect and translate to English
            result = translator.translate_text(text, target_lang='EN-GB')
            if result.text.lower() != text.lower():
                return f"🇬🇧 {result.text}"
        except Exception as e:
            logger.error(f"->EN failed: {e}")

        return None

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued"""
    welcome_message = (
        "👋 Hello! I'm your Portuguese-English translator bot!\n\n"
        "I will automatically translate:\n"
        "🇬🇧 English messages to Portuguese 🇵🇹\n"
        "🇵🇹 Portuguese messages to English 🇬🇧\n\n"
        "Just start typing in either language!"
    )
    await update.message.reply_text(welcome_message)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    try:
        # Only process text messages from non-bot users
        if not update.message or not update.message.text or update.message.from_user.is_bot:
            return

        # Try to translate
        translated = await translate_text(update.message.text)
        if translated:
            await update.message.reply_text(translated)
    except Exception as e:
        logger.error(f"Message handling failed: {e}")

def main() -> None:
    """Start the bot"""
    try:
        # Get bot token
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            logger.error("TELEGRAM_BOT_TOKEN not found")
            return

        # Create and configure bot
        app = Application.builder().token(token).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Start bot
        logger.info("Starting bot...")
        app.run_polling(drop_pending_updates=True)

    except Exception as e:
        logger.error(f"Bot startup error: {e}")

if __name__ == '__main__':
    main()
