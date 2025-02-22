import os
import logging
import sys
from typing import Optional
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from deepl import Translator
from dotenv import load_dotenv

# Configure basic logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def validate_api_keys():
    """Validate API keys are present and well-formed"""
    telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
    deepl_key = os.getenv('DEEPL_API_KEY')
    
    if not telegram_token:
        logger.error("TELEGRAM_BOT_TOKEN not found")
        return False
    
    if not deepl_key:
        logger.error("DEEPL_API_KEY not found")
        return False
    
    # Log partial keys for debugging (safely)
    logger.info(f"Telegram token found (starts with): {telegram_token[:10]}...")
    logger.info(f"DeepL key found (starts with): {deepl_key[:10]}...")
    
    return True

if not validate_api_keys():
    sys.exit(1)

# Initialize DeepL translator
try:
    translator = Translator(os.getenv('DEEPL_API_KEY'))
    # Test with both target languages
    logger.info("Testing DeepL translator...")
    en_test = translator.translate_text("teste", target_lang="EN-GB")
    pt_test = translator.translate_text("test", target_lang="PT-PT")
    logger.info(f"DeepL test translations successful: 'teste' -> '{en_test.text}', 'test' -> '{pt_test.text}'")
except Exception as e:
    logger.error(f"Failed to initialize/test translator: {str(e)}", exc_info=True)
    sys.exit(1)

async def translate_text(text: str) -> Optional[str]:
    """Translate text between English and Portuguese"""
    try:
        # Clean the text
        text = ' '.join(text.strip().split())
        if not text:
            return None

        logger.info(f"Attempting to translate text: {text}")

        # First try to detect the language
        try:
            # Try Portuguese to English first
            result = translator.translate_text(text, target_lang='EN-GB')
            detected_lang = result.detected_source_language
            logger.info(f"Detected language: {detected_lang}")
            
            if detected_lang.upper().startswith('PT'):
                if result.text.lower() != text.lower():
                    logger.info(f"Translated PT->EN: {result.text}")
                    return result.text
            elif detected_lang.upper().startswith('EN'):
                # If English detected, translate to Portuguese
                result = translator.translate_text(text, target_lang='PT-PT')
                if result.text.lower() != text.lower():
                    logger.info(f"Translated EN->PT: {result.text}")
                    return result.text
            else:
                logger.info(f"Unexpected language detected: {detected_lang}")
                # Try both translations anyway
                pt_result = translator.translate_text(text, target_lang='PT-PT')
                en_result = translator.translate_text(text, target_lang='EN-GB')
                if pt_result.text.lower() != text.lower():
                    return pt_result.text
                if en_result.text.lower() != text.lower():
                    return en_result.text
        except Exception as e:
            logger.error(f"Translation error: {str(e)}", exc_info=True)
            return None

        logger.info("No translation needed (text might be in the same language)")
        return None

    except Exception as e:
        logger.error(f"Translation failed: {str(e)}", exc_info=True)
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
    try:
        await update.message.reply_text(welcome_message)
        logger.info(f"Start command handled for user {update.effective_user.id}")
    except Exception as e:
        logger.error(f"Error handling start command: {str(e)}", exc_info=True)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle incoming messages"""
    try:
        # Only process text messages from non-bot users
        if not update.message or not update.message.text or update.message.from_user.is_bot:
            logger.info("Skipping message: not a text message or from a bot")
            return

        logger.info(f"Processing message from user {update.effective_user.id}: {update.message.text}")

        # Try to translate
        translated = await translate_text(update.message.text)
        if translated:
            logger.info(f"Sending translation to chat {update.message.chat_id}")
            try:
                await context.bot.send_message(
                    chat_id=update.message.chat_id,
                    text=translated,
                    reply_to_message_id=update.message.message_id
                )
                logger.info("Translation sent successfully")
            except Exception as e:
                logger.error(f"Failed to send translation: {str(e)}", exc_info=True)
        else:
            logger.info("No translation was needed or translation failed")
    except Exception as e:
        logger.error(f"Message handling failed: {str(e)}", exc_info=True)

def main() -> None:
    """Start the bot"""
    try:
        # Create and configure bot
        app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

        # Start bot
        logger.info("Starting bot...")
        app.run_polling(
            drop_pending_updates=True,
            allowed_updates=["message"],
            stop_signals=None,  # Disable signal handling
            pool_timeout=30.0,  # Increase timeout
            read_timeout=30.0,
            write_timeout=30.0
        )

    except Exception as e:
        logger.error(f"Bot startup error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
