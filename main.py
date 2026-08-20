import logging
import urllib.parse
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from google import genai

# Telegram Token နဲ့ ပုံထဲက Gemini API Key
TELEGRAM_BOT_TOKEN = "8970292140:AAG7vL6attDLED3kUKgXeAmO-bRF63PIwcg"
GEMINI_API_KEY = "AQ.Ab8RN6IcbF3CGnk-LPXyl0yrQNV7BD0eVLni_N9zKVhkOVBEtg"

# Gemini Client initialize လုပ်ခြင်း
client = genai.Client(api_key=GEMINI_API_KEY)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "မင်္ဂလာပါ! Gemini AI Bot မှ ကြိုဆိုပါတယ်။\n\n"
        "• စာမေးရန်: တိုက်ရိုက် စာရေးပြီး ပို့ပါ။\n"
        "• ပုံထုတ်ရန်: `/draw <ပုံဖော်ပြချက်>` ဟု ရေးပါ။"
    )
    await update.message.reply_text(welcome_text)

# Gemini 1.5 Flash ဖြင့် စာကြောင်းများ ဖြေကြားပေးခြင်း
async def chat_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=user_message,
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        await update.message.reply_text("တောင်းပန်ပါတယ်၊ Gemini API ချိတ်ဆက်မှု အမှားတစ်ခု ရှိနေပါသည်။")

# Pollinations.ai ဖြင့် အခမဲ့ ပုံထုတ်ပေးခြင်း
async def draw_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("ကျေးဇူးပြု၍ ပုံထုတ်ရန် စာသားထည့်ပါ။\nဥပမာ - `/draw a cyber cat`")
        return

    prompt = " ".join(context.args)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="upload_photo")

    try:
        encoded_prompt = urllib.parse.quote(prompt)
        image_url = f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=1024&seed=42&model=flux"
        await update.message.reply_photo(photo=image_url, caption=f"Prompt: {prompt}")
    except Exception as e:
        await update.message.reply_text("ပုံထုတ်ရာတွင် အမှားတစ်ခု ရှိသွားပါသည်။")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("draw", draw_image))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat_ai))

    print("Bot is successfully running...")
    app.run_polling()
