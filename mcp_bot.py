import os
import logging
import httpx
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

# 🔐 Load environment variables
load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/chat")

if not TELEGRAM_TOKEN:
    raise ValueError("❌ TELEGRAM_TOKEN not set in .env")

# ✅ Logging setup
logging.basicConfig(
    filename="chat_logs.txt",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# 🟢 /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I’m your MCP Bot. Ask me anything!")

# 💬 Handle messages and call MCP server
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    user_id = update.effective_user.id

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                MCP_SERVER_URL,
                json={"model": "openrouter/cypher-alpha:free", "message": user_message}
            )
            response.raise_for_status()
            reply = response.json().get("response", "⚠️ No reply from MCP.")
    except Exception as e:
        logging.error(f"[User:{user_id}] MCP Server Error: {e}")
        reply = "🚨 MCP server is unavailable."

    await update.message.reply_text(reply)
    logging.info(f"[User:{user_id}] {user_message} → {reply}")

# 🚀 Main bot runner
def main():
    print("🤖 Starting MCP Telegram bot...")
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
