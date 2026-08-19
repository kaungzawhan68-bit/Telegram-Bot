import os
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from googletrans import Translator

# Telegram Bot Token ကို ဒီမှာ ထည့်ပါ
TOKEN = "8811845324:AAGeX31hSOlJnccGWqglYaYNnYACm_y4ZxA" # သင့် Token အပြည့်အစုံ ပြန်ထည့်ပါ

translator = Translator()

# Render အတွက် Web Server (Port Error မတက်အောင်)
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Translation Bot is running alive!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! ဘာသာပြန်ချင်တဲ့ စာသား (သို့မဟုတ် အင်္ဂလိပ်စာ) ကို ပို့ပေးပါ။ မြန်မာလို အလိုအလျောက် ဘာသာပြန်ပေးပါမည်။ 🇲🇲"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if not text:
        return

    await update.message.reply_text("ဘာသာပြန်ပေးနေပါသည်... ⏳")

    try:
        # Google Translate ကို သုံးပြီး မြန်မာလို ဘာသာပြန်ခြင်း
        loop = asyncio.get_event_loop()
        translated = await loop.run_in_executor(
            None, lambda: translator.translate(text, dest='my')
        )

        await update.message.reply_text(translated.text)

    except Exception as e:
        await update.message.reply_text(f"ဘာသာပြန်ရာတွင် အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်: {str(e)}")

if __name__ == '__main__':
    Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Translate Bot is running...")
    app.run_polling()
