import os
import json
import threading
import time
from telebot import TeleBot, types
from yt_dlp import YoutubeDL
from flask import Flask

print("✅ البوت بدأ التشغيل...")
API_TOKEN = "8223563446:AAFpPKZJUxb3gHsiK58D75iIvjsVg7O5vjY"
bot = TeleBot(API_TOKEN)
CHANNEL_USERNAME = "Sirya_n"
OWNER_ID = 7106025090
KEEP_ALIVE_ID = 7623026338

app = Flask(__name__)

users = {}
points = {}

def load_data():
    global users, points
    if os.path.exists("users.json"):
        with open("users.json", "r") as f:
            users = json.load(f)
    if os.path.exists("points.json"):
        with open("points.json", "r") as f:
            points = json.load(f)

def save_data():
    with open("users.json", "w") as f:
        json.dump(users, f)
    with open("points.json", "w") as f:
        json.dump(points, f)

load_data()

if not os.path.exists("downloads"):
    os.makedirs("downloads")

def get_lang(user_id):
    return users.get(str(user_id), {}).get("lang", "ar")

def t(key, lang):
    texts = {
        "start": {
            "ar": "🎶 أرسل اسم الأغنية أو رابط الفيديو",
            "fa": "🎶 نام آهنگ یا لینک ویدیو را ارسال کنید",
            "en": "🎶 Send the song name or video link"
        },
        "subscribe": {
            "ar": "📛 يجب الاشتراك بالقناة لاستخدام البوت",
            "fa": "📛 برای استفاده از ربات باید عضو کانال شوید",
            "en": "📛 You must subscribe to the channel to use the bot"
        },
        "choose_format": {
            "ar": "اختر التنسيق المطلوب:",
            "fa": "فرمت مورد نظر را انتخاب کنید:",
            "en": "Choose your preferred format:"
        },
        "vip": {
            "ar": "🎉 مبروك! أصبحت VIP",
            "fa": "🎉 تبریک! شما VIP شدید",
            "en": "🎉 Congrats! You are now VIP"
        },
        "points": {
            "ar": "🌟 نقاطك: {} نقطة\n🎯 تحتاج {} لتصبح VIP",
            "fa": "🌟 امتیاز شما: {} امتیاز\n🎯 {} امتیاز تا VIP شدن باقی مانده",
            "en": "🌟 Your points: {}\n🎯 You need {} more to become VIP"
        },
        "broadcast_prompt": {
            "ar": "📢 أرسل نص الرسالة التي تريد إذاعتها لجميع المستخدمين:",
            "fa": "📢 متن پیام برای ارسال به همه کاربران را بفرستید:",
            "en": "📢 Send the message you want to broadcast to all users:"
        },
        "broadcast_sent": {
            "ar": "✅ تم إرسال الإذاعة لجميع المستخدمين.",
            "fa": "✅ پیام به همه کاربران ارسال شد.",
            "en": "✅ Broadcast sent to all users."
        },
        "admin_panel": {
            "ar": "🛠️ لوحة تحكم المطور:\nاختر إجراء من الأزرار أدناه.",
            "fa": "🛠️ پنل مدیریت:\nیکی از گزینه‌های زیر را انتخاب کنید.",
            "en": "🛠️ Admin Panel:\nChoose an action below."
        }
    }
    return texts.get(key, {}).get(lang, "")

def is_subscribed(user_id):
    try:
        member = bot.get_chat_member(f"@{CHANNEL_USERNAME}", user_id)
        return member.status in ["member", "administrator", "creator"]
    except Exception:
        return False

def is_vip(user_id):
    return points.get(str(user_id), 0) >= 1000 or users.get(str(user_id), {}).get("invites", 0) >= 10

@bot.message_handler(commands=['start'])
def start_handler(message):
    print("📩 تم استقبال أمر /start من:", message.from_user.id)
    user_id = str(message.from_user.id)
    users[user_id] = users.get(user_id, {"lang": "ar", "invites": 0})
    points[user_id] = points.get(user_id, 0)
    save_data()

    lang = get_lang(user_id)
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("🎵 تحميل أغنية", "🎁 تجميع النقاط")
    keyboard.add("📊 دعواتي", "🆘 مساعدة")
    keyboard.add("🔐 تفعيل VIP", "📊 الإحصائيات")
    if message.from_user.id == OWNER_ID:
        keyboard.add("📢 إرسال إذاعة", "🔄 إعادة تشغيل", "🛠️ لوحة المطور")

    bot.send_message(message.chat.id, t("start", lang), reply_markup=keyboard)

@bot.message_handler(func=lambda m: m.text == "🛠️ لوحة المطور")
def admin_panel(message):
    if message.from_user.id == OWNER_ID:
        lang = get_lang(message.from_user.id)
        panel = types.ReplyKeyboardMarkup(resize_keyboard=True)
        panel.add("📢 إرسال إذاعة", "📊 الإحصائيات")
        panel.add("🔐 تفعيل VIP", "🔄 إعادة تشغيل")
        panel.add("⬅️ رجوع")
        bot.send_message(message.chat.id, t("admin_panel", lang), reply_markup=panel)

@bot.message_handler(func=lambda m: m.text == "⬅️ رجوع")
def back_to_main(message):
    start_handler(message)

@bot.message_handler(commands=['lang'])
def change_lang(message):
    user_id = str(message.from_user.id)
    lang = message.text.split(" ", 1)[-1]
    if lang in ["ar", "fa", "en"]:
        users[user_id]["lang"] = lang
        save_data()
        bot.send_message(message.chat.id, "✅ Language changed" if lang == "en" else "✅ تم تغيير اللغة" if lang == "ar" else "✅ زبان تغییر یافت")

@bot.message_handler(commands=['points'])
def show_points(message):
    user_id = str(message.from_user.id)
    pts = points.get(user_id, 0)
    lang = get_lang(user_id)
    bot.send_message(message.chat.id, t("points", lang).format(pts, 1000 - pts))

@bot.message_handler(func=lambda m: m.text == "📊 دعواتي")
def my_invites(message):
    user_id = str(message.from_user.id)
    invites = users.get(user_id, {}).get("invites", 0)
    bot.send_message(message.chat.id, f"📊 عدد الأصدقاء الذين دخلوا من رابطك: {invites}")

@bot.message_handler(func=lambda m: m.text == "🎁 تجميع النقاط")
def invite_button(message):
    user_id = str(message.from_user.id)
    link = f"https://t.me/{bot.get_me().username}?start={user_id}"
    bot.send_message(message.chat.id, f"📨 هذا رابط الدعوة الخاص بك:\n{link}\n✅ أرسله لأصدقائك، وكل دخول يمنحك 100 نقطة")

@bot.message_handler(func=lambda m: m.text == "🆘 مساعدة")
def help_button(message):
    lang = get_lang(message.from_user.id)
    bot.send_message(message.chat.id, t("start", lang))

@bot.message_handler(func=lambda m: m.text == "🔐 تفعيل VIP")
def activate_vip(message):
    user_id = str(message.from_user.id)
    points[user_id] = 1000
    save_data()
    bot.send_message(message.chat.id, t("vip", get_lang(user_id)))

@bot.message_handler(func=lambda m: m.text == "🔄 إعادة تشغيل")
def restart_bot(message):
    if message.from_user.id == OWNER_ID:
        bot.send_message(message.chat.id, "🔄 سيتم إعادة تشغيل البوت...")
        os._exit(1)

@bot.message_handler(func=lambda m: m.text == "📢 إرسال إذاعة")
def ask_broadcast(message):
    if message.from_user.id == OWNER_ID:
        lang = get_lang(message.from_user.id)
        bot.send_message(message.chat.id, t("broadcast_prompt", lang))
        bot.register_next_step_handler(message, send_broadcast)

def send_broadcast(message):
    lang = get_lang(message.from_user.id)
    for uid in users:
        try:
            bot.send_message(int(uid), message.text)
        except Exception:
            continue
    bot.send_message(message.chat.id, t("broadcast_sent", lang))

@bot.message_handler(func=lambda m: m.text == "📊 الإحصائيات")
def stats(message):
    if message.from_user.id == OWNER_ID:
        total = len(users)
        vip_count = sum(1 for uid in users if is_vip(uid))
        bot.send_message(message.chat.id, f"📊 عدد المستخدمين: {total}\n👑 عدد الـ VIP: {vip_count}")

@bot.message_handler(func=lambda m: m.text == "🎵 تحميل أغنية")
def ask_song(message):
    bot.send_message(message.chat.id, "🎶 أرسل اسم الأغنية أو رابط الفيديو")

@bot.message_handler(func=lambda m: True)
def handle_song(message):
    user_id = str(message.from_user.id)
    lang = get_lang(user_id)
    if not is_subscribed(message.from_user.id) and not is_vip(message.from_user.id):
        bot.send_message(message.chat.id, t("subscribe", lang))
        return
    query = message.text
    btn = types.InlineKeyboardMarkup()
    btn.add(
        types.InlineKeyboardButton(text="🎵 MP3", callback_data="mp3|" + query),
        types.InlineKeyboardButton(text="🎥 فيديو", callback_data="video|" + query)
    )
    bot.send_message(message.chat.id, t("choose_format", lang), reply_markup=btn)

@bot.callback_query_handler(func=lambda c: "|" in c.data)
def process_callback(call):
    user_id = str(call.from_user.id)
    lang = get_lang(user_id)
    if not is_subscribed(call.from_user.id) and not is_vip(call.from_user.id):
        bot.send_message(call.message.chat.id, t("subscribe", lang))
        return
    mode, query = call.data.split("|", 1)
    bot.send_message(call.message.chat.id, "⏳ جاري التحميل...")

    ydl_opts = {
        'format': 'bestaudio/best' if mode == "mp3" else 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }] if mode == "mp3" else []
    }

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch:{query}", download=True)
            if info and isinstance(info, dict) and "entries" in info:
                entries = info.get("entries", [])
            else:
                entries = [info]
            if not entries:
                bot.send_message(call.message.chat.id, "❌ لم يتم العثور على نتائج.")
                return
            video = entries[0]
            file_path = ydl.prepare_filename(video)
            if mode == "mp3":
                file_path = file_path.rsplit(".", 1)[0] + ".mp3"
        if not os.path.exists(file_path):
            bot.send_message(call.message.chat.id, "❌ الملف غير موجود.")
            return
        with open(file_path, "rb") as f:
            if mode == "mp3":
                bot.send_audio(call.message.chat.id, f)
            else:
                bot.send_video(call.message.chat.id, f)
        try:
            os.remove(file_path)
        except Exception:
            pass
        points[user_id] = points.get(user_id, 0) + 3
        save_data()
        if is_vip(user_id):
            bot.send_message(call.message.chat.id, t("vip", lang))
    except Exception as e:
        bot.send_message(call.message.chat.id, f"❌ خطأ أثناء التحميل: {e}")

# 🔄 الحفاظ على نشاط البوت كل دقيقة
def keep_alive():
    while True:
        try:
            bot.send_message(KEEP_ALIVE_ID, "✅ البوت ما زال يعمل")
        except Exception as e:
            print("خطأ في الإرسال:", e)
        time.sleep(60)

threading.Thread(target=keep_alive, daemon=True).start()

if __name__ == "__main__":
    bot.polling(none_stop=True)
    app.run(host="0.0.0.0", port=8080)
