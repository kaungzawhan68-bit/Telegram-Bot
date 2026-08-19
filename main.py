import os
import re
import json
import asyncio
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# Telegram Bot Token ကို ဒီမှာ ထည့်ပါ
TOKEN = "8811845324:AAGeX31hSOlJnccGWqglYaYNnYACm_y4ZxA" # သင့် Token အပြည့်အစုံ ပြန်ထည့်ပါ

# Render အတွက် Web Server
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running alive!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ!ငါလိုးမသား YouTube ဗီဒီယို Link ကို ပို့ပေးပါ။ စကားပြော စာသားများ (Transcript) ထုတ်ပေးပါမည်။"
    )

def get_youtube_subtitles(url):
    # yt-dlp အသုံးပြု၍ Subtitle ဆွဲယူခြင်း
    cmd = [
        "yt-dlp",
        "--write-sub",
        "--write-auto-sub",
        "--sub-lang", "en,my,ja,ko",
        "--skip-download",
        "--sub-format", "json3",
        "-o", "sub_file",
        url
    ]
    
    # ဖိုင်အဟောင်းရှိရင် ဖျက်ပါ
    if os.path.exists("sub_file.en.json3"):
        os.remove("sub_file.en.json3")

    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # Subtitle ဖိုင်များကို ရှာဖွေခြင်း
    sub_file = None
    for file in os.listdir("."):
        if file.startswith("sub_file") and file.endswith(".json3"):
            sub_file = file
            break

    if not sub_file:
        return None

    try:
        with open(sub_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        full_text = []
        for event in data.get("events", []):
            if "segs" in event:
                for seg in event["segs"]:
                    utf8_str = seg.get("utf8", "").strip()
                    if utf8_str and utf8_str != "\n":
                        full_text.append(utf8_str)
        
        # ခေတ္တဖန်တီးထားသော ဖိုင်ကို ပြန်ဖျက်ပါ
        os.remove(sub_file)
        return " ".join(full_text)
    except Exception:
        if os.path.exists(sub_file):
            os.remove(sub_file)
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "youtube.com" not in text and "youtu.be" not in text:
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Link ပို့ပေးပါ။")
        return

    await update.message.reply_text("စာသားများကို ဆွဲယူနေပါသည်... ခဏစောင့်ပါ။ ⏳")

    try:
        # Sync function ကို Async ထဲမှ ခေါ်ယူခြင်း
        loop = asyncio.get_event_loop()
        transcript_text = await loop.run_in_executor(None, get_youtube_subtitles, text)

        if not transcript_text:
            await update.message.reply_text("ဒီဗီဒီယိုအတွက် Subtitle/Transcript မတွေ့ရှိပါ သို့မဟုတ် ရယူ၍ မရပါ။")
            return

        # စာသားရှည်ပါက အပိုင်းလိုက် ခွဲပို့ပေးခြင်း
        if len(transcript_text) > 4000:
            for i in range(0, len(transcript_text), 4000):
                await update.message.reply_text(transcript_text[i:i+4000])
        else:
            await update.message.reply_text(transcript_text)

    except Exception as e:
        await update.message.reply_text(f"အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်: {str(e)}")

if __name__ == '__main__':
    Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
