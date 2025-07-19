import telebot
import os
import yt_dlp
import whisper
import random

BOT_TOKEN = "8138350200:AAFsaRnzZA_ogAD44TjJ-1MY9YgPvfTwJ2k"
CHANNELS_FILE = "tiktok_channels.txt"
VIDEO_IDS_FILE = "video_ids.txt"

bot = telebot.TeleBot(BOT_TOKEN)

# إعداد الملفات
open(CHANNELS_FILE, "a").close()
open(VIDEO_IDS_FILE, "a").close()
os.makedirs("downloads", exist_ok=True)

def extract_username(link):
    try:
        # إزالة أي بارامترات إضافية مثل ?_t=... أو &_r=...
        clean_link = link.split("?")[0].strip()

        # استخراج الجزء بعد tiktok.com/
        username_part = clean_link.split("tiktok.com/")[1]

        # إزالة الشرطة المائلة الأخيرة إن وجدت
        if username_part.endswith("/"):
            username_part = username_part[:-1]

        # إزالة الـ @ إن وجدت
        if username_part.startswith("@"):
            username_part = username_part[1:]

        return username_part
    except Exception:
        return None

def download_tiktok_video(url):
    ydl_opts = {
        'outtmpl': os.path.join("downloads", '%(id)s.%(ext)s'),
        'format': 'mp4',
        'quiet': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info), info["id"], info.get("duration", 0), info.get("view_count", 0)

def extract_audio_text(video_path):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result['text']

@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📄 عرض القنوات المحفوظة", "🎲 فيديو عشوائي")
    markup.row("📁 عرض الفيديوهات المحفوظة")
    bot.send_message(message.chat.id, "👋 أرسل رابط قناة تيك توك لحفظه أو اختر من الخيارات:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📄 عرض القنوات المحفوظة")
def list_channels(message):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        links = f.read().strip()
    if links:
        bot.send_message(message.chat.id, f"📋 القنوات:\n\n{links}")
    else:
        bot.send_message(message.chat.id, "📭 لا توجد قنوات محفوظة.")

@bot.message_handler(func=lambda message: message.text == "📁 عرض الفيديوهات المحفوظة")
def list_videos(message):
    with open(VIDEO_IDS_FILE, "r", encoding="utf-8") as f:
        vids = f.read().strip()
    if vids:
        bot.send_message(message.chat.id, f"🎞️ الفيديوهات:\n\n{vids}")
    else:
        bot.send_message(message.chat.id, "📭 لا توجد فيديوهات محفوظة.")

@bot.message_handler(func=lambda message: message.text == "🎲 فيديو عشوائي")
def handle_random_video(message):
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        links = f.read().splitlines()
    if not links:
        bot.send_message(message.chat.id, "❌ لا توجد قنوات محفوظة.")
        return

    chosen = random.choice(links)
    username = extract_username(chosen)
    if not username:
        bot.send_message(message.chat.id, "❌ تعذر استخراج اسم القناة.")
        return

    bot.send_message(message.chat.id, f"🔍 يتم فحص قناة: @{username}")

    try:
        ydl_opts = {'quiet': True, 'extract_flat': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"https://www.tiktok.com/@{username}", download=False)
            entries = info.get('entries', [])
            for entry in entries:
                vid = entry['id']
                if vid in open(VIDEO_IDS_FILE).read():
                    continue
                video_url = f"https://www.tiktok.com/@{username}/video/{vid}"
                path, vid_id, duration, views = download_tiktok_video(video_url)
                if 50 <= duration <= 90 and views >= 1_000_000:
                    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
                    markup.row("🎧 استخراج النص", "⬇️ تنزيل الفيديو")
                    bot.send_message(message.chat.id, f"🎥 تم اختيار الفيديو:\n{video_url}", reply_markup=markup)
                    bot.register_next_step_handler(message, lambda m: handle_action(m, path, vid_id))
                    return
        bot.send_message(message.chat.id, "⚠️ لم أجد فيديو مناسب.")
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ حدث خطأ: {e}")

def handle_action(message, video_path, video_id):
    if message.text == "⬇️ تنزيل الفيديو":
        with open(video_path, "rb") as f:
            bot.send_video(message.chat.id, f)
    elif message.text == "🎧 استخراج النص":
        text = extract_audio_text(video_path)
        bot.send_message(message.chat.id, f"📜 النص:\n{text}")
    with open(VIDEO_IDS_FILE, "a", encoding="utf-8") as f:
        f.write(video_id + "\n")

@bot.message_handler(func=lambda message: "tiktok.com/" in message.text)
def save_tiktok_channel(message):
    full_link = message.text.strip()
    new_username = extract_username(full_link)
    if not new_username:
        bot.send_message(message.chat.id, "❌ لم أتمكن من تحديد اسم القناة.")
        return
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        saved = [extract_username(l) for l in f.read().splitlines()]
    if new_username in saved:
        bot.send_message(message.chat.id, "✅ هذه القناة محفوظة مسبقًا.")
        return
    with open(CHANNELS_FILE, "a", encoding="utf-8") as f:
        f.write(full_link + "\n")
    bot.send_message(message.chat.id, "✅ تم حفظ القناة.")

if __name__ == "__main__":
    print("✅ البوت يعمل...")
    bot.infinity_polling()
