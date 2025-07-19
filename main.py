import telebot
import os
import requests
import base64

# بيانات البوت وGitHub
BOT_TOKEN = "8138350200:AAFsaRnzZA_ogAD44TjJ-1MY9YgPvfTwJ2k"
GITHUB_TOKEN = "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"
REPO_NAME = "lologaby2/bootaltegthia"
BRANCH = "main"
FILE_PATH = "storage/tiktok_channels.txt"

bot = telebot.TeleBot(BOT_TOKEN)

# إنشاء المجلد والملف إن لم تكن موجودة
os.makedirs("storage", exist_ok=True)
open(FILE_PATH, "a").close()

# استخراج اسم المستخدم من رابط القناة
def extract_username(link):
    try:
        return link.split("tiktok.com/")[1].split("?")[0].split("/")[0]
    except:
        return None

# رفع الملف إلى GitHub
def upload_to_github(file_path):
    url = f"https://api.github.com/repos/{REPO_NAME}/contents/{file_path}"
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    content_b64 = base64.b64encode(content.encode("utf-8")).decode("utf-8")

    # الحصول على SHA الحالي إن وجد
    r = requests.get(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"})
    sha = r.json().get("sha", "")

    data = {
        "message": "update tiktok channels",
        "content": content_b64,
        "branch": BRANCH,
    }
    if sha:
        data["sha"] = sha

    r = requests.put(url, headers={"Authorization": f"Bearer {GITHUB_TOKEN}"}, json=data)
    print("GitHub Response:", r.status_code, r.text)  # لمعرفة سبب الفشل
    return r.status_code == 201 or r.status_code == 200

# رسالة الترحيب
@bot.message_handler(commands=["start"])
def send_welcome(message):
    markup = telebot.types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "👋 أرسل رابط قناة تيك توك لحفظه.", reply_markup=markup)

# استقبال الروابط ومعالجتها
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

    uploaded = upload_to_github(FILE_PATH)
    if uploaded:
        bot.send_message(message.chat.id, "✅ تم حفظ القناة ورفعها إلى GitHub.")
    else:
        bot.send_message(message.chat.id, "⚠️ تم حفظ القناة لكن فشل رفعها إلى GitHub.")

# تشغيل البوت
if __name__ == "__main__":
    print("✅ البوت يعمل...")
    bot.infinity_polling()
