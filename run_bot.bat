@echo off
echo 🟢 Activating virtual environment...
call venv\Scripts\activate.bat

echo 🚀 Running MCP Telegram bot...
python mcp_bot.py

pause