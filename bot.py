import os
import logging
import tempfile
import whisper
import asyncio
from typing import Optional, Tuple
from telegram import Update
from telegram.ext import Application, MessageHandler, CommandHandler, filters, ContextTypes
from deepl import Translator
from dotenv import load_dotenv

# Configure detailed logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Whisper model
model = whisper.load_model("base")

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

        # Get both translations
        pt_text = None
        en_text = None

        try:
            # Translate to Portuguese
            result = translator.translate_text(text, target_lang='PT-PT')
            if result.text.lower() != text.lower():
                pt_text = result.text
        except Exception as e:
            logger.error(f"->PT failed: {e}")

        try:
            # Translate to English
            result = translator.translate_text(text, target_lang='EN-GB')
            if result.text.lower() != text.lower():
                en_text = result.text
        except Exception as e:
            logger.error(f"->EN failed: {e}")

        # Return both translations if they're different from input
        if pt_text and en_text:
            return f"🇬🇧 {en_text}\n🇵🇹 {pt_text}"
        elif pt_text:
            return f"🇵🇹 {pt_text}"
        elif en_text:
            return f"🇬🇧 {en_text}"

        return None

    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return None

async def transcribe_audio(file_path: str) -> Tuple[str, str]:
    """Transcribe audio file and detect its language"""
    try:
        logger.info(f"Starting transcription of file: {file_path}")
        # Run transcription in a thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: model.transcribe(file_path))
        logger.info(f"Transcription successful: {result['text'][:100]}...")
        return result["text"], result["language"]
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        return "", ""

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
        if not update.message:
            logger.info("No message in update")
            return
            
        if update.message.from_user.is_bot:
            logger.info("Ignoring bot message")
            return

        # Log message type
        logger.info(f"Received message type: voice={bool(update.message.voice)}, "
                   f"audio={bool(update.message.audio)}, video={bool(update.message.video)}, "
                   f"video_note={bool(update.message.video_note)}, text={bool(update.message.text)}")

        # Handle text messages
        if update.message.text:
            translated = await translate_text(update.message.text)
            if translated:
                await update.message.reply_text(translated)
            return

        # Handle voice/audio/video messages
        if update.message.voice or update.message.audio or update.message.video or update.message.video_note:
            # Send a "processing" message
            processing_msg = await update.message.reply_text("📡 Processing audio...")
            logger.info("Started processing audio/video message")

            try:
                # Get file ID
                file_id = None
                if update.message.voice:
                    file_id = update.message.voice.file_id
                elif update.message.audio:
                    file_id = update.message.audio.file_id
                elif update.message.video:
                    file_id = update.message.video.file_id
                elif update.message.video_note:
                    file_id = update.message.video_note.file_id

                logger.info(f"Got file_id: {file_id}")

                # Get the file
                file = await context.bot.get_file(file_id)
                logger.info(f"Got file object: {file.file_path}")

                # Download to temp file
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_file:
                    await file.download_to_drive(temp_file.name)
                    logger.info(f"Downloaded file to: {temp_file.name}")
                    
                    # Transcribe
                    logger.info("Starting transcription...")
                    text, detected_lang = await transcribe_audio(temp_file.name)
                    logger.info(f"Transcription complete. Text: {text[:100]}... Lang: {detected_lang}")
                    
                    # Clean up temp file
                    os.unlink(temp_file.name)
                    logger.info("Cleaned up temp file")

                    if text:
                        # Translate the transcription
                        translated = await translate_text(text)
                        response = f"🎤 Transcription:\n{text}"
                        if translated:
                            response += f"\n\n🔁 Translation:\n{translated}"
                        
                        await processing_msg.edit_text(response)
                    else:
                        await processing_msg.edit_text("❌ Could not transcribe the audio")

            except Exception as e:
                logger.error(f"Audio processing failed: {e}")
                await processing_msg.edit_text("❌ Error processing audio")

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
