import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from downloader import download_video, get_video_info
from config import BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── /start ──────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎬 *YouTube Downloader Bot*\n\n"
        "Send me any YouTube link and I'll download it for you!\n\n"
        "Supported formats:\n"
        "• 🎥 Video (360p / 720p / 1080p)\n"
        "• 🎵 Audio only (MP3)\n\n"
        "Just paste a URL to get started 👇",
        parse_mode="Markdown"
    )

# ── /help ────────────────────────────────────────────────────────────────
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *How to use:*\n\n"
        "1. Paste a YouTube URL\n"
        "2. Choose your preferred quality\n"
        "3. Wait for the download ⏳\n\n"
        "⚠️ Max file size: 50MB (Telegram limit)\n"
        "For longer videos, use audio-only mode.",
        parse_mode="Markdown"
    )

# ── Handle YouTube URL ───────────────────────────────────────────────────
async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    # Basic URL validation
    if "youtube.com" not in url and "youtu.be" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube URL.")
        return

    msg = await update.message.reply_text("🔍 Fetching video info...")

    try:
        info = get_video_info(url)
        title = info.get("title", "Unknown Title")
        duration = info.get("duration", 0)
        mins, secs = divmod(duration, 60)

        # Store URL in user_data for callback use
        context.user_data["url"] = url
        context.user_data["title"] = title

        keyboard = [
            [InlineKeyboardButton("🎵 Audio MP3", callback_data="audio")],
            [InlineKeyboardButton("📱 360p", callback_data="360")],
            [InlineKeyboardButton("💻 720p HD", callback_data="720")],
            [InlineKeyboardButton("🖥️ 1080p FHD", callback_data="1080")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await msg.edit_text(
            f"🎬 *{title}*\n"
            f"⏱ Duration: {mins}m {secs}s\n\n"
            "Choose download quality:",
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

    except Exception as e:
        logger.error(f"Error fetching info: {e}")
        await msg.edit_text("❌ Could not fetch video info. Check the URL and try again.")

# ── Handle Quality Selection ─────────────────────────────────────────────
async def handle_quality(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    quality = query.data
    url = context.user_data.get("url")
    title = context.user_data.get("title", "video")

    if not url:
        await query.edit_message_text("❌ Session expired. Please send the URL again.")
        return

    quality_labels = {
        "audio": "🎵 Audio MP3",
        "360": "📱 360p",
        "720": "💻 720p HD",
        "1080": "🖥️ 1080p FHD"
    }
    await query.edit_message_text(
        f"⏬ Downloading {quality_labels[quality]}...\n"
        f"📹 {title}\n\n"
        "This may take a moment ⏳"
    )

    try:
        file_path = download_video(url, quality)

        if quality == "audio":
            await query.message.reply_audio(
                audio=open(file_path, "rb"),
                title=title,
                caption=f"🎵 {title}"
            )
        else:
            await query.message.reply_video(
                video=open(file_path, "rb"),
                caption=f"🎬 {title} ({quality}p)",
                supports_streaming=True
            )

        await query.edit_message_text(f"✅ Done! Enjoy your {'audio' if quality == 'audio' else 'video'} 🎉")

        # Cleanup
        import os
        os.remove(file_path)

    except Exception as e:
        logger.error(f"Download error: {e}")
        await query.edit_message_text(
            "❌ Download failed. Possible reasons:\n"
            "• File too large (>50MB)\n"
            "• Video unavailable or restricted\n"
            "• Try a lower quality or audio-only"
        )

# ── Main ─────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    app.add_handler(CallbackQueryHandler(handle_quality))

    logger.info("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
