from fastapi import FastAPI, Request
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram import Update
import telegram
import httpx, logging, os
from dotenv import load_dotenv

# Load env vars
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000/chat")
BOT_URL = os.getenv("BOT_URL")  # e.g., https://your-bot-name.onrender.com

application = ApplicationBuilder().token(TOKEN).build()

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
                json={"model": "mistralai/mistral-7b-instruct:free", "message": user_message}
            )
            response.raise_for_status()
            data = response.json() 
           
            print(f"📦 MCP raw response: {data}")  # ✅ Debug print
            logging.info(f"[User:{user_id}] MCP raw response: {data}")
            reply = data.get("response") or data.get("message") or (
                data.get("choices", [{}])[0].get("message", {}).get("content")
            )
            if not reply:
                raise ValueError("❌ 'response' key missing in MCP reply.")
    except Exception as e:
        logging.error(f"[User:{user_id}] MCP Server Error: {e}")
        reply = "🚨 MCP server is unavailable."

    await update.message.reply_text(reply)
    logging.info(f"[User:{user_id}] {user_message} → {reply}")

# Handlers (reuse your existing ones)
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# FastAPI app
app = FastAPI()

@app.on_event("startup")
async def set_webhook():
    await application.bot.set_webhook(f"{BOT_URL}/webhook")

@app.post("/webhook")
async def webhook(request: Request):
    update = Update.de_json(await request.json(), application.bot)
    await application.process_update(update)
    return "ok"
