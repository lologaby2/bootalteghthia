import os
import random
import telebot
import yt_dlp
import whisper
import threading
import time

BOT_TOKEN = "8138350200:AAFsaRnzZA_ogAD44TjJ-1MY9YgPvfTwJ2k"

CHANNELS_FILE = "tiktok_channels.txt"
VIDEO_IDS_FILE = "video_ids.txt"

BTN_CHANNELS = "📄 عرض القنوات المحفوظة"
BTN_VIDEOIDS = "📁 عرض video_ids"
BTN_RANDOM = "🎲 فيديو عشوائي"

bot = telebot.TeleBot(BOT_TOKEN)

open(CHANNELS_FILE, "a").close()
open(VIDEO_IDS_FILE, "a").close()
os.makedirs("downloads", exist_ok=True)

VIDEO_CACHE = {}

# مؤقت لإيقاف البوت بعد 10 دقائق من عدم النشاط
last_activity_time = time.time()
def monitor_inactivity():
    while True:
        time.sleep(60)
        if time.time() - last_activity_time > 600:
            print("⏹️ لا يوجد نشاط منذ 10 دقائق، يتم إيقاف البوت.")
            os._exit(0)
threading.Thread(target=monitor_inactivity, daemon=True).start()

def extract_username(link: str):
    try:
        clean_link = link.split("?")[0].strip()
        username_part = clean_link.split("tiktok.com/")[1]
        if username_part.endswith("/"):
            username_part = username_part[:-1]
        if username_part.startswith("@"):
            username_part = username_part[1:]
        return username_part
    except Exception:
        return None

def download_tiktok_video(url: str):
    ydl_opts = {
        "outtmpl": os.path.join("downloads", "%(id)s.%(ext)s"),
        "format": "mp4",
        "quiet": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return (
            ydl.prepare_filename(info),
            info["id"],
            info.get("duration", 0),
            info.get("view_count", 0),
        )

def extract_audio_text(video_path: str):
    model = whisper.load_model("base")
    result = model.transcribe(video_path)
    return result["text"]

@bot.message_handler(commands=["start"])
def send_welcome(message):
    global last_activity_time
    last_activity_time = time.time()
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row(BTN_CHANNELS, BTN_RANDOM)
    markup.row(BTN_VIDEOIDS)
    bot.send_message(
        message.chat.id,
        "👋 أرسل رابط قناة تيك توك لحفظه أو اختر من الخيارات:",
        reply_markup=markup,
    )

@bot.message_handler(func=lambda message: message.text == BTN_CHANNELS)
def list_channels(message):
    global last_activity_time
    last_activity_time = time.time()
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        links = f.read().strip()
    if links:
        bot.send_message(message.chat.id, f"📋 القنوات:\n\n{links}")
    else:
        bot.send_message(message.chat.id, "📭 لا توجد قنوات محفوظة.")

@bot.message_handler(func=lambda message: message.text == BTN_VIDEOIDS)
def list_videos(message):
    global last_activity_time
    last_activity_time = time.time()
    with open(VIDEO_IDS_FILE, "r", encoding="utf-8") as f:
        vids = f.read().strip()
    if vids:
        bot.send_message(message.chat.id, f"🎞️ video_ids:\n\n{vids}")
    else:
        bot.send_message(message.chat.id, "📭 لا توجد فيديوهات محفوظة.")

@bot.message_handler(func=lambda message: message.text == BTN_RANDOM)
def handle_random_video(message):
    global last_activity_time
    last_activity_time = time.time()
    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        links = [l for l in f.read().splitlines() if l.strip()]

    if not links:
        bot.send_message(message.chat.id, "❌ لا توجد قنوات محفوظة.")
        return

    random.shuffle(links)

    with open(VIDEO_IDS_FILE, "r", encoding="utf-8") as f:
        done_ids = set(f.read().splitlines())

    for chosen in links:
        username = extract_username(chosen)
        if not username:
            continue

        bot.send_message(message.chat.id, f"🔍 يتم فحص قناة: @{username}")

        try:
            ydl_opts = {"quiet": True, "extract_flat": True}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"https://www.tiktok.com/@{username}", download=False)
                entries = info.get("entries", [])

                for entry in entries:
                    vid = entry["id"]
                    if vid in done_ids:
                        continue

                    video_url = f"https://www.tiktok.com/@{username}/video/{vid}"
                    path, vid_id, duration, views = download_tiktok_video(video_url)

                    if 50 <= duration <= 90 and views >= 2_000_000:
                        VIDEO_CACHE[vid_id] = {"path": path, "url": video_url}

                        markup = telebot.types.InlineKeyboardMarkup()
                        markup.add(
                            telebot.types.InlineKeyboardButton("🎧 استخراج النص", callback_data=f"tr|{vid_id}"),
                            telebot.types.InlineKeyboardButton("⬇️ تنزيل الفيديو", callback_data=f"dl|{vid_id}"),
                            telebot.types.InlineKeyboardButton("✅ حفظ الفيديو فقط", callback_data=f"save|{vid_id}")
                        )

                        bot.send_message(
                            message.chat.id,
                            f"🎥 تم اختيار الفيديو:\n{video_url}",
                            reply_markup=markup,
                        )
                        return

        except Exception:
            continue

    bot.send_message(message.chat.id, "⚠️ لم أجد أي فيديو مناسب في كل القنوات.")

@bot.callback_query_handler(func=lambda call: True)
def handle_callbacks(call):
    global last_activity_time
    last_activity_time = time.time()
    try:
        action, vid_id = call.data.split("|", 1)
        data = VIDEO_CACHE.get(vid_id)

        if not data:
            bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية الفيديو. أعد الاختيار.")
            return

        path = data["path"]

        if action == "dl":
            with open(path, "rb") as f:
                bot.send_video(call.message.chat.id, f)
            bot.answer_callback_query(call.id, "✅ تم إرسال الفيديو")

        elif action == "tr":
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "🧠 جاري استخراج النص...")
            text = extract_audio_text(path)
            bot.send_message(call.message.chat.id, f"📜 النص:\n{text}")

        elif action == "save":
            with open(VIDEO_IDS_FILE, "a", encoding="utf-8") as f:
                f.write(vid_id + "\n")
            bot.answer_callback_query(call.id, "✅ تم حفظ الفيديو")

    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ خطأ أثناء التنفيذ: {e}")

@bot.message_handler(func=lambda message: "tiktok.com/" in message.text)
def save_tiktok_channel(message):
    global last_activity_time
    last_activity_time = time.time()
    full_link = message.text.strip()
    new_username = extract_username(full_link)
    if not new_username:
        bot.send_message(message.chat.id, "❌ لم أتمكن من تحديد اسم القناة.")
        return

    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        saved = [extract_username(l) for l in f.read().splitlines() if l.strip()]

    if new_username in saved:
        bot.send_message(message.chat.id, "✅ هذه القناة محفوظة مسبقًا.")
        return

    with open(CHANNELS_FILE, "a", encoding="utf-8") as f:
        f.write(full_link + "\n")

    bot.send_message(message.chat.id, "✅ تم حفظ القناة.")

if __name__ == "__main__":
    print("✅ البوت يعمل...")
    bot.polling(none_stop=True, interval=0, timeout=60)
