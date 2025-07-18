import telebot
import os
import random
import time

BOT_TOKEN = "8138350200:AAFsaRnzZA_ogAD44TjJ-1MY9YgPvfTwJ2k"
bot = telebot.TeleBot(BOT_TOKEN)

MUSIC_FOLDER = "storage/music"
CHANNELS_FILE = "storage/tiktok_channels.txt"
CATEGORIES = ["حزينة", "سعيدة", "غامضة", "انسانية", "عاطفية", "دراما"]

os.makedirs(MUSIC_FOLDER, exist_ok=True)
for cat in CATEGORIES:
    os.makedirs(os.path.join(MUSIC_FOLDER, cat), exist_ok=True)
os.makedirs("storage", exist_ok=True)
open(CHANNELS_FILE, "a").close()

@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("🎵 إرسال موسيقى", "📥 إرسال قناة تيكتوك", "🔀 موسيقى عشوائية")
    bot.send_message(message.chat.id, "أهلاً بك، اختر وظيفة:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "🎵 إرسال موسيقى")
def ask_music_category(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in CATEGORIES:
        markup.add(cat)
    bot.send_message(message.chat.id, "اختر تصنيف الموسيقى:", reply_markup=markup)
    bot.register_next_step_handler(message, wait_for_audio)

def wait_for_audio(message):
    if message.text not in CATEGORIES:
        bot.send_message(message.chat.id, "يرجى اختيار تصنيف من القائمة.")
        return
    category = message.text
    bot.send_message(message.chat.id, f"أرسل الآن ملف الموسيقى لتصنيفه ضمن: {category}")
    bot.register_next_step_handler(message, lambda m: save_music_file(m, category))

def save_music_file(message, category):
    if not message.audio and not message.voice and not message.document:
        bot.send_message(message.chat.id, "الملف غير صالح. يرجى إرسال ملف mp3.")
        return
    file_id = message.audio.file_id if message.audio else message.document.file_id
    file_info = bot.get_file(file_id)
    downloaded = bot.download_file(file_info.file_path)
    filename = f"{category}_{file_id}.mp3"
    path = os.path.join(MUSIC_FOLDER, category, filename)
    with open(path, "wb") as f:
        f.write(downloaded)
    bot.send_message(message.chat.id, "✅ تم حفظ الموسيقى بنجاح.")

def extract_username(link):
    try:
        return link.split("tiktok.com/")[1].split("?")[0].split("/")[0]
    except:
        return None

@bot.message_handler(func=lambda message: "tiktok.com/" in message.text)
def save_tiktok_channel(message):
    full_link = message.text.strip()
    new_username = extract_username(full_link)

    if not new_username or not new_username.startswith("@"):
        bot.send_message(message.chat.id, "❌ لم أتمكن من تحديد اسم القناة.")
        return

    with open(CHANNELS_FILE, "r", encoding="utf-8") as f:
        saved_links = f.read().splitlines()

    saved_usernames = [extract_username(link) for link in saved_links]

    if new_username in saved_usernames:
        bot.send_message(message.chat.id, "✅ هذه القناة محفوظة مسبقًا.")
        return

    with open(CHANNELS_FILE, "a", encoding="utf-8") as f:
        f.write(full_link + "\n")

    bot.send_message(message.chat.id, "✅ تم حفظ قناة تيك توك.")

@bot.message_handler(func=lambda m: m.text == "🔀 موسيقى عشوائية")
def ask_category_for_random(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    for cat in CATEGORIES:
        markup.add(cat)
    bot.send_message(message.chat.id, "اختر التصنيف:", reply_markup=markup)
    bot.register_next_step_handler(message, send_random_music)

def send_random_music(message):
    if message.text not in CATEGORIES:
        bot.send_message(message.chat.id, "❌ تصنيف غير صحيح.")
        return
    category = message.text
    folder = os.path.join(MUSIC_FOLDER, category)
    files = os.listdir(folder)
    if not files:
        bot.send_message(message.chat.id, "❌ لا يوجد موسيقى في هذا التصنيف.")
        return
    file_path = os.path.join(folder, random.choice(files))
    with open(file_path, "rb") as f:
        bot.send_audio(message.chat.id, f)

if __name__ == "__main__":
    print("✅ جاري تشغيل البوت على Railway...")
    time.sleep(3)
    bot.infinity_polling()

@bot.message_handler(commands=['show_channels'])
def show_channels(message):
    try:
        with open("storage/tiktok_channels.txt", "r", encoding="utf-8") as f:
            links = f.readlines()
        if links:
            bot.send_message(message.chat.id, "📋 روابط القنوات:\n" + "".join(links))
        else:
            bot.send_message(message.chat.id, "📭 لا توجد قنوات محفوظة بعد.")
    except FileNotFoundError:
        bot.send_message(message.chat.id, "❌ لم يتم العثور على ملف القنوات.")
