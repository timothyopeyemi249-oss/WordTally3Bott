import os
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ============ CONFIGURATION ============
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")

# Enable logging to see what's happening
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ CORE FUNCTIONS ============

def count_words(text: str) -> dict:
    """Count words, characters, sentences, and paragraphs in a text."""
    if not text:
        return {"words": 0, "chars": 0, "sentences": 0, "paragraphs": 0}
    
    # Remove extra whitespace for accurate counting
    clean_text = re.sub(r'\s+', ' ', text).strip()
    
    words = len(re.findall(r'\b\w+\b', text))
    chars = len(text)
    
    # Count sentences by . ! ? endings
    sentences = len(re.findall(r'[.!?]+', text))
    if sentences == 0 and text.strip():  # If no punctuation, treat as one sentence
        sentences = 1
    
    # Count paragraphs by newline or double spaces
    paragraphs = len([p for p in text.split('\n') if p.strip()]) if '\n' in text else 1
    if not text.strip():
        paragraphs = 0
    
    return {
        "words": words,
        "chars": chars,
        "sentences": sentences,
        "paragraphs": paragraphs
    }

def generate_summary(stats: dict) -> str:
    """Format the statistics into a readable message."""
    return (
        f"📊 **Text Analysis Summary**\n\n"
        f"📝 **Words:** `{stats['words']}`\n"
        f"🔤 **Characters:** `{stats['chars']}`\n"
        f"📖 **Sentences:** `{stats['sentences']}`\n"
        f"📄 **Paragraphs:** `{stats['paragraphs']}`\n\n"
        f"💡 _Tip: Send me a document (.txt or .md) for batch analysis!_"
    )

# ============ COMMAND HANDLERS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command - welcome message."""
    welcome_message = (
        f"👋 **Hello! I'm WordTally3Bot!**\n\n"
        f"I can count words, characters, sentences, and paragraphs in your text.\n\n"
        f"**How to use me:**\n"
        f"• Send me any text message\n"
        f"• Send a `.txt` or `.md` file\n"
        f"• Use /help for more options\n\n"
        f"🚀 _Powered by Railway & GitHub_"
    )
    keyboard = [
        [InlineKeyboardButton("📊 Example", callback_data="example")],
        [InlineKeyboardButton("❓ Help", callback_data="help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /help command - show all features."""
    help_text = (
        f"🆘 **Help & Commands**\n\n"
        f"**Available Commands:**\n"
        f"• /start - Welcome message\n"
        f"• /help - Show this help menu\n"
        f"• /stats - Get your usage stats\n\n"
        f"**What I Can Do:**\n"
        f"✅ Count words in any text\n"
        f"✅ Count characters (including spaces)\n"
        f"✅ Count sentences and paragraphs\n"
        f"✅ Analyze .txt and .md files\n\n"
        f"**Made with ❤️ using python-telegram-bot**"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /stats command - show user statistics."""
    # You can expand this to track user data in a database
    stats_text = (
        f"📈 **Your Stats**\n\n"
        f"👤 User ID: `{update.effective_user.id}`\n"
        f"🏷️ Username: @{update.effective_user.username or 'N/A'}\n"
        f"📅 First seen: Just now!\n\n"
        f"💾 _Database integration coming soon!_"
    )
    await update.message.reply_text(stats_text, parse_mode="Markdown")

# ============ MESSAGE HANDLERS ============

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages - count words and reply."""
    if not update.message or not update.message.text:
        return
    
    text = update.message.text
    stats = count_words(text)
    response = generate_summary(stats)
    
    # If the text is very long, show only the first 50 chars
    preview = text[:50] + "..." if len(text) > 50 else text
    response += f"\n\n📌 **Preview:** `{preview}`"
    
    await update.message.reply_text(response, parse_mode="Markdown")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle document uploads - read .txt and .md files."""
    document = update.message.document
    file_name = document.file_name or "unknown.txt"
    
    # Only process text files
    if not (file_name.endswith('.txt') or file_name.endswith('.md') or file_name.endswith('.csv')):
        await update.message.reply_text(
            f"❌ I can only read `.txt` and `.md` files. You sent: `{file_name}`",
            parse_mode="Markdown"
        )
        return
    
    # Send a processing message
    processing_msg = await update.message.reply_text("⏳ Reading your file...")
    
    try:
        # Download the file
        file = await document.get_file()
        file_content = await file.download_as_bytearray()
        text = file_content.decode('utf-8', errors='ignore')
        
        # Check if file is empty
        if not text.strip():
            await processing_msg.edit_text("⚠️ The file is empty. Please send a non-empty file.")
            return
        
        # Count words
        stats = count_words(text)
        response = generate_summary(stats)
        response += f"\n\n📄 **File:** `{file_name}`"
        
        # Show first 100 characters as preview
        preview = text[:100] + "..." if len(text) > 100 else text
        response += f"\n\n📌 **Preview:** `{preview}`"
        
        await processing_msg.edit_text(response, parse_mode="Markdown")
    
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        await processing_msg.edit_text(f"❌ Error reading file: {str(e)}")

# ============ CALLBACK QUERY HANDLERS ============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button callbacks."""
    query = update.callback_query
    await query.answer()  # Acknowledge the button press
    
    if query.data == "example":
        example_text = "This is an example sentence. Here's another one! And a third one for good measure."
        stats = count_words(example_text)
        response = generate_summary(stats)
        response += f"\n\n📌 **Example Text:** `{example_text}`"
        await query.edit_message_text(response, parse_mode="Markdown")
    
    elif query.data == "help":
        help_text = (
            f"🆘 **Quick Help**\n\n"
            f"• Send any text to analyze it\n"
            f"• Upload .txt or .md files\n"
            f"• Use /stats to see your activity\n"
            f"• Use /start to restart the bot\n\n"
            f"Click the 🔙 button to go back."
        )
        keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="back_to_start")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(help_text, reply_markup=reply_markup, parse_mode="Markdown")
    
    elif query.data == "back_to_start":
        welcome_message = (
            f"👋 **Welcome back!**\n\n"
            f"Send me any text to analyze, or use /help for options."
        )
        keyboard = [
            [InlineKeyboardButton("📊 Example", callback_data="example")],
            [InlineKeyboardButton("❓ Help", callback_data="help")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(welcome_message, reply_markup=reply_markup, parse_mode="Markdown")

# ============ ERROR HANDLER ============

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors and notify user."""
    logger.error(f"Update {update} caused error {context.error}")
    
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "⚠️ Something went wrong. Please try again later."
        )

# ============ MAIN ============

if __name__ == '__main__':
    if not BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN environment variable not set!")
        exit(1)
    
    logger.info("🚀 Starting WordTally3Bot...")
    
    # Build the application
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add command handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("stats", stats_command))
    
    # Add message handlers
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    
    # Add callback handler for inline buttons
    app.add_handler(CallbackQueryHandler(button_callback))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # Start the bot with long polling
    logger.info("✅ Bot is running! Waiting for messages...")
    app.run_polling()
