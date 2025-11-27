import os
import sqlite3
import time
from flask import Flask, request
import telebot
from telebot import types
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
BOT_TOKEN = "8346801600:AAGwVSdfvls42KHFtXwbcZhPzBNVEg8rU9g"  # O'zgartirmang yoki .env ga o'tkazing
bot = telebot.TeleBot(BOT_TOKEN)
ADMIN_ID = 2051084228

# RAILWAY UCHUN MUHIM: Doimiy disk yo'li
DB_PATH = os.getenv("DB_PATH", "/app/data/users.db")  # Railway volume

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, join_date TEXT)''')
    conn.commit()
    conn.close()

init_db()

def add_user(user):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?)",
              (user.id, user.username or "—", user.first_name or "—", now))
    conn.commit()
    conn.close()

def get_user_count():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

# Qolgan kodlar (obuna, menyu, linklar) — avvalgidek qoldirdim, faqat DB_PATH ishlatilmoqda
REQUIRED_CHANNELS = [
    {"name": "1-kanal", "username": "@bsb_chsb_javoblari1"},
    {"name": "2-kanal", "username": "@chsb_original"},
]

LINKS = {
    "bsb_5": "https://www.test-uz.ru/sor_uz.php?klass=5", "bsb_6": "https://www.test-uz.ru/sor_uz.php?klass=6",
    "bsb_7": "https://www.test-uz.ru/sor_uz.php?klass=7", "bsb_8": "https://www.test-uz.ru/sor_uz.php?klass=8",
    "bsb_9": "https://www.test-uz.ru/sor_uz.php?klass=9", "bsb_10": "https://www.test-uz.ru/sor_uz.php?klass=10",
    "bsb_11": "https://www.test-uz.ru/sor_uz.php?klass=11",
    "chsb_5": "https://www.test-uz.ru/soch_uz.php?klass=5", "chsb_6": "https://www.test-uz.ru/soch_uz.php?klass=6",
    "chsb_7": "https://www.test-uz.ru/soch_uz.php?klass=7", "chsb_8": "https://www.test-uz.ru/soch_uz.php?klass=8",
    "chsb_9": "https://www.test-uz.ru/soch_uz.php?klass=9", "chsb_10": "https://www.test-uz.ru/soch_uz.php?klass=10",
    "chsb_11": "https://www.test-uz.ru/soch_uz.php?klass=11",
}

def is_subscribed(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            status = bot.get_chat_member(ch["username"], user_id).status
            if status in ["left", "kicked"]: return False
        except: return False
    return True

def subscription_buttons():
    markup = types.InlineKeyboardMarkup(row_width=1)
    for ch in REQUIRED_CHANNELS:
        markup.add(types.InlineKeyboardButton(ch["name"], url=f"https://t.me/{ch['username'][1:]}"))
    markup.add(types.InlineKeyboardButton("Tekshirish", callback_data="check_subs"))
    return markup

def main_menu_markup():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add("BSB JAVOBLARI", "CHSB JAVOBLARI", "Reklama xizmati")
    return markup

def sub_menu_markup(typ):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    for i in range(5, 12, 2):
        markup.row(f"{i}-sinf {typ}", f"{i+1}-sinf {typ}")
    markup.add("Asosiy menyu")
    return markup

@bot.message_handler(commands=['start'])
def start_handler(message):
    add_user(message.from_user)
    welcome = f"""Assalomu alaykum {message.from_user.first_name}

Botimizga xush kelibsiz

BSB & CHSB javoblari — hammasi tekin

Kanallarga obuna bo‘ling"""
    bot.send_message(message.chat.id, welcome, reply_markup=subscription_buttons())

@bot.callback_query_handler(func=lambda call: call.data == "check_subs")
def check_subscriptions(call):
    if is_subscribed(call.from_user.id):
        bot.edit_message_text("Obuna tasdiqlandi!", call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Asosiy menyu:", reply_markup=main_menu_markup())
    else:
        bot.answer_callback_query(call.id, "Obuna bo‘lmagansiz!", show_alert=True)

@bot.message_handler(func=lambda m: m.text in ["BSB JAVOBLARI", "CHSB JAVOBLARI"])
def select_menu(message):
    if not is_subscribed(message.from_user.id):
        return bot.send_message(message.chat.id, "Obuna bo‘ling!", reply_markup=subscription_buttons())
    typ = "BSB" if "BSB" in message.text else "CHSB"
    bot.send_message(message.chat.id, f"{typ} sinfni tanlang:", reply_markup=sub_menu_markup(typ))

@bot.message_handler(func=lambda m: "sinf" in m.text)
def send_link(message):
    if not is_subscribed(message.from_user.id):
        return bot.send_message(message.chat.id, "Obuna bo‘ling!", reply_markup=subscription_buttons())
    grade = message.text.split("-")[0].strip()
    typ = "bsb" if "BSB" in message.text else "chsb"
    key = f"{typ}_{grade}"
    link = LINKS.get(key)
    if link:
        bot.send_message(message.chat.id, f"{message.text}\n\nLink: {link}")
    else:
        bot.send_message(message.chat.id, "Link topilmadi.")

@bot.message_handler(func=lambda m: m.text == "Asosiy menyu")
def back(message): bot.send_message(message.chat.id, "Asosiy menyu:", reply_markup=main_menu_markup())

@bot.message_handler(func=lambda m: m.text == "Reklama xizmati")
def reklama(message): bot.send_message(message.chat.id, "Reklama: @BAR_xn")

# ADMIN
@bot.message_handler(commands=['admin'])
def admin(message):
    if message.from_user.id != ADMIN_ID: return
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("Xabar yuborish", "Statistika", "Chiqish")
    bot.send_message(message.chat.id, "Admin panel", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "Statistika" and m.from_user.id == ADMIN_ID)
def stats(message): bot.reply_to(message, f"Foydalanuvchilar: {get_user_count():,} ta")

@bot.message_handler(func=lambda m: m.text == "Xabar yuborish" and m.from_user.id == ADMIN_ID)
def broadcast_start(message):
    msg = bot.send_message(message.chat.id, "Xabarni yuboring\n/cancel — bekor qilish")
    bot.register_next_step_handler(msg, broadcast_process)

def broadcast_process(message):
    if message.text == "/cancel": return bot.reply_to(message, "Bekor qilindi")
    users = get_all_users()
    total = len(users)
    success = failed = 0
    status = bot.send_message(message.chat.id, f"0/{total}")
    for i, uid in enumerate(users):
        try:
            bot.copy_message(uid, message.chat.id, message.message_id)
            success += 1
        except: failed += 1
        if (i+1) % 10 == 0 or i == total-1:
            bot.edit_message_text(f"{success+failed}/{total}\n{success} | {failed}", message.chat.id, status.message_id)
            time.sleep(0.33)
    bot.edit_message_text(f"Broadcast tugadi!\n{success} | {failed}", message.chat.id, status.message_id)

# Webhook
@app.route(f"/{BOT_TOKEN}", methods=['POST'])
def webhook():
    update = telebot.types.Update.de_json(request.stream.read().decode("utf-8"))
    bot.process_new_updates([update])
    return "OK", 200

@app.route("/")
def index(): return "Bot ishlayapti!"

if __name__ == "__main__":
    bot.remove_webhook()
    time.sleep(1)
    bot.set_webhook(url=f"https://{os.getenv('RAILWAY_STATIC_URL') or 'your-project.up.railway.app'}/{BOT_TOKEN}")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
