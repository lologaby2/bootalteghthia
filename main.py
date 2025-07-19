import telebot
import os

BOT_TOKEN = "8138350200:AAFsaRnzZA_ogAD44TjJ-1MY9YgPvfTwJ2k"
FILE_PATH = "tiktok_channels.txt"

bot = telebot.TeleBot(BOT_TOKEN)
open(FILE_PATH, "a").close()

def extract_username(link):
    try:
        return link.split("tiktok.com/")[1].split("?")[0].split("/")[0]
    except:
        return None

@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row("📄 عرض القنوات المحفوظة")
    bot.send_message(message.chat.id, "👋 أرسل رابط قناة تيك توك لحفظه.", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "📄 عرض القنوات المحفوظة")
def list_channels(message):
    with open(FILE_PATH, "r", encoding="utf-8") as f:
        links = f.read().strip()
    if links:
        bot.send_message(message.chat.id, f"📋 هذه القنوات المحفوظة:\n\n{links}")
    else:
        bot.send_message(message.chat.id, "📭 لا توجد أي روابط محفوظة حتى الآن.")

@bot.message_handler(func=lambda message: "tiktok.com/" in message.text)
def save_tiktok_channel(message):
    full_link = message.text.strip()
    new_username = extract_username(full_link)

    if not new_username or not new_username.startswith("@"):
        bot.send_message(message.chat.id, "❌ لم أتمكن من تحديد اسم القناة من الرابط.")
        return

    with open(FILE_PATH, "r", encoding="utf-8") as f:
        saved_links = f.read().splitlines()
    saved_usernames = [extract_username(link) for link in saved_links]

    if new_username in saved_usernames:
        bot.send_message(message.chat.id, "✅ هذه القناة محفوظة مسبقًا.")
        return

    with open(FILE_PATH, "a", encoding="utf-8") as f:
        f.write(full_link + "\n")

    bot.send_message(message.chat.id, "✅ تم حفظ القناة.")

if __name__ == "__main__":
    print("✅ البوت يعمل...")
    bot.infinity_polling()
