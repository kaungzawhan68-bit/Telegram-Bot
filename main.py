import os
import re
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# Telegram Bot Token ကို ဒီမှာ ထည့်ပါ
TOKEN = "8811845324:AAGeX31hSOlJnccGWqglYaYNnYACm_y4ZxA" # သင့် Token အပြည့်အစုံ ပြန်ထည့်ပါ

# Render အတွက် Web Server အသေးလေး
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running alive!")

def run_health_check_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    server.serve_forever()

# YouTube URL မှ Video ID ထုတ်ယူခြင်း
def extract_video_id(url):
    pattern = r"(?:v=|\/|be\/|embed\/)([a-zA-Z0-9_-]{11})"
    match = re.search(pattern, url)
    return match.group(1) if match else None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "မင်္ဂလာပါ! YouTube ဗီဒီယို Link ကို ပို့ပေးပါ။ စကားပြော စာသားများ (Transcript) ထုတ်ပေးပါမည်။"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    video_id = extract_video_id(text)

    if not video_id:
        await update.message.reply_text("ကျေးဇူးပြု၍ မှန်ကန်သော YouTube Link ပို့ပေးပါ။")
        return

    await update.message.reply_text("စာသားများကို ဆွဲယူနေပါသည်... ခဏစောင့်ပါ။ ⏳")

    try:
        # Version အသစ်အတွက် ပြင်ထားသောနေရာ
        ytt = YouTubeTranscriptApi()
        transcript_list = ytt.fetch(video_id, languages=['en', 'my', 'ja', 'ko'])
        full_text = " ".join([item['text'] for item in transcript_list])

        if len(full_text) > 4000:
            for i in range(0, len(full_text), 4000):
                await update.message.reply_text(full_text[i:i+4000])
        else:
            await update.message.reply_text(full_text)

    except TranscriptsDisabled:
        await update.message.reply_text("ဒီဗီဒီယိုမှာ Subtitle/Transcript ပိတ်ထားပါသဖြင့် စာသားထုတ်ယူ၍ မရပါ။")
    except NoTranscriptFound:
        await update.message.reply_text("ဒီဗီဒီယိုအတွက် Subtitle/Transcript မတွေ့ရှိပါ။")
    except Exception as e:
        await update.message.reply_text(f"အမှားတစ်ခု ဖြစ်ပေါ်ခဲ့သည်: {str(e)}")

if __name__ == '__main__':
    Thread(target=run_health_check_server, daemon=True).start()

    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()
