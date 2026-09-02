# -*- coding: utf-8 -*-
"""
Delta Tour Premium — Telegram bot
Yopiq kanal uchun tarif tanlash va to'lov havolasini yuboruvchi bot.

ISHGA TUSHIRISH:
1. pip install pyTelegramBotAPI
2. Pastdagi BOT_TOKEN, ADMIN_USERNAME, PAYMENT_LINK qiymatlarini o'zgartiring
3. python delta_tour_bot.py
"""

import os
import time
import json
import datetime
import threading
import telebot
from telebot import types
from flask import Flask

# ==========================================
# SOZLAMALAR — shu joylarni o'zgartiring
# ==========================================

BOT_TOKEN = "8550889867:AAHxX6aW2c3mvT1suArtd4X81u2twX26QFk"

# To'lov qilingandan keyin mijoz murojaat qiladigan admin username (@siz)
ADMIN_USERNAME = "@deltatour_admin"

# Click/Payme to'lov sahifangiz havolasi
PAYMENT_LINK = "https://payme.uz/fallback/merchant/?id=6981e2d99949957019e20311"

# Kanal invite linki (obuna tasdiqlangach mijozga shu link yuboriladi)
CHANNEL_INVITE_LINK = "https://t.me/+b3wNF7hhzvliZDUy"

# /start bosilganda yuboriladigan dumaloq (video note) tanishtiruv videosi.
# Fayl botning kodi bilan bir papkada bo'lishi kerak (masalan: welcome.mp4)
WELCOME_VIDEO_NOTE = "welcome.mp4"

# Telefon raqamlar (mijoz "raqam"/"telefon"/"bog'lanish" deb yozganda yuboriladi)
PHONE_NUMBERS = ["+998 90 823 90 00", "+998 90 814 90 00"]

# Ofis joylashuvi (Google Maps koordinatalari)
OFFICE_LATITUDE = 41.363040428422835
OFFICE_LONGITUDE = 69.2754007070276

# Manzil videosi (bot papkasida bo'lishi kerak)
OFFICE_VIDEO = "office_location.mp4"

# "Biz haqimizda" matni
ABOUT_US_TEXT = (
    "🦅 <b>Delta Tour</b> — 2021 yildan buyon xizmatingizda, 5 yildan ortiq "
    "tajriba bilan.\n\n"
    "🏆 2023 yil — Sharm el-Shayx yo'nalishi bo'yicha sotuvlar yetakchisi\n"
    "🏆 2024-2025 yillar — Turkiya yo'nalishi bo'yicha sotuvlar yetakchisi\n\n"
    "Biz Turkiya, Sharm el-Shayx, Vetnam, Tailand, Bali, Kuala-Lumpur, Gruziya "
    "va Ozarbayjon yo'nalishlari bo'yicha turlar tashkil qilamiz. Bundan tashqari, "
    "dunyoning istalgan shahriga shaxsiy va ekskursion turlar, jamoaviy va "
    "korporativ sayohatlar bilan ham shug'ullanamiz.\n\n"
    "Har bir sayohat — bizning tajribamiz, sizning ishonchingiz bilan boshlanadi.\n\n"
    "👥 10 000+ mijozimiz allaqachon unutilmas sayohatga chiqdi, shundan 500+ "
    "mijozimiz shengen vizasini muvaffaqiyatli qo'lga kiritdi ✅"
)

# ==========================================
# STIKERLAR — turli holatlar uchun
# (Har biri qaysi holatga mos kelishini o'zingiz tekshirib, kerak bo'lsa
# quyidagi joylashuvni almashtiring — masalan STICKERS["welcome"] ni
# STICKERS["vip"] bilan almashtirsangiz bo'ladi)
# ==========================================

STICKERS = {
    "welcome": "CAACAgIAAxkBAAMVaphWMNhWdNoPCmrPZN0TLFokWv0AAphfAAJ_f6BIFLmS5SAPVpY9BA",  # Assalomu alaykum
    "va_alaykum": "CAACAgIAAxkBAAMraphd6TEI-oHGjLFwrom9Th5_2uQAAulkAAIbQ5hIFf4B0VZddsY9BA",  # Va alaykum salom
    "logo": "CAACAgIAAxkBAAM5aphefS4TWBBUK1u7tNCWBbFqR9wAAkpiAAK5MqFINeXuV-cjHCo9BA",  # Delta Tour logotipi
    "thanks": "CAACAgIAAxkBAAMWaphWOBWIcsQ4QrG5JDZWft06xXkAAoVrAAIUlKFIel6jfB7bAAFsPQQ",  # Rahmat
    "thanks_for_choosing": "CAACAgIAAxkBAAM7aphejsxNbq3Znc9Vt4dXZNQiwecAAr5oAAIrYslIuBB-rOIIE9U9BA",  # Bizni tanlaganingiz uchun rahmat
    "holiday": "CAACAgIAAxkBAAMzapheOkH7FpbuJI0GguDh4rXapAYAAstiAAJZv6FIse5EY2-k1BM9BA",  # Bayram muborak
    "qurbon_hayit": "CAACAgIAAxkBAAMxapheIbJ2WZfNAgiAUlMmmVReXMUAAvBtAAI956FIZuzDgJjY9xk9BA",  # Qurbon hayiti
    "sorry": "CAACAgIAAxkBAAMvapheEphkSO-8rOVwkBLiSIwUqYkAAqdgAAJUC6hIOGW2PX2pgPY9BA",  # Uzr so'rash
    "phone": "CAACAgIAAxkBAAMtaphd--zLu8HRsSnEE7OypsYpeF0AAsBiAAKph6lIu6WR5l0NNWo9BA",  # Telefon raqamlar
    "labbay": "CAACAgIAAxkBAAM1apheU-wOB9DYcby2q1lZrvvZybMAAvtnAAJxvqFIiMIHOtI1xVg9BA",  # Labbay
}

# ==========================================
# BAYRAMLAR — avtomatik tabriklash
# Format: "OY-KUN": (matn, stiker_kaliti)
# ==========================================

HOLIDAYS = {
    "01-01": (
        "🎉 <b>Yangi yil bilan tabriklaymiz!</b>\n\n"
        "Delta Tour jamoasi sizga yangi yilda yangi manzillar, unutilmas "
        "sayohatlar va baxtli lahzalar tilaydi! 🥂✈️",
        "holiday",
    ),
    "03-21": (
        "🌸 <b>Navro'z bayrami muborak bo'lsin!</b>\n\n"
        "Yangi bahor, yangi umidlar va yangi sayohatlar bilan! "
        "Delta Tour jamoasidan issiq tabriklar. 🌿",
        "holiday",
    ),
    "09-01": (
        "🇺🇿 <b>Mustaqillik kuningiz muborak bo'lsin!</b>\n\n"
        "Delta Tour jamoasi sizni mamlakatimiz mustaqilligi bayrami bilan "
        "tabriklaydi! 🎊",
        "holiday",
    ),
    # ⚠️ MUHIM: Qurbon hayiti sanasi har yili o'zgaradi (hijriy taqvim bo'yicha).
    # Har yili aniq sanani bilib, shu formatda ("OY-KUN") yangilab turing.
    # 2027 yil uchun taxminiy sana - albatta tasdiqlab, to'g'irlang:
    "06-17": (
        "🕌 <b>Qurbon hayiti muborak bo'lsin!</b>\n\n"
        "Delta Tour jamoasi sizni muqaddas Qurbon hayiti bayrami bilan "
        "tabriklaydi! Uy-joyingizga tinchlik, oilangizga baraka tilaymiz.",
        "qurbon_hayit",
    ),
}

# Foydalanuvchilar ro'yxati saqlanadigan fayl (bayram tabriklari uchun)
USERS_FILE = "bot_users.json"
# Qaysi bayram qaysi yilda yuborilganini saqlash uchun fayl
HOLIDAY_LOG_FILE = "holiday_log.json"

# ==========================================
# TARIFLAR
# ==========================================

TARIFFS = {
    "standard": {
        "name": "STANDART",
        "period": "1 oy (oyma-oy)",
        "price": "150 000 so'm",
        "people": "O'zingiz + 2 kishigacha",
        "gifts": "—",
    },
    "premium": {
        "name": "PREMIUM",
        "period": "3 oy",
        "price": "600 000 so'm",
        "people": "O'zingiz + 5 kishigacha",
        "gifts": "Yostiqcha + esdalik sovg'a",
    },
    "vip": {
        "name": "VIP",
        "period": "6 oy",
        "price": "2 300 000 so'm",
        "people": "O'zingiz + 15 kishigacha",
        "gifts": "Esm + yostiqcha + maxsus esdalik + ryukzak",
    },
}

bot = telebot.TeleBot(BOT_TOKEN)

# Tarif tanlagan, lekin hali "To'lov qildim" bosmagan foydalanuvchilarni kuzatish uchun
# Format: {user_id: {"tariff": "premium", "confirmed": False}}
pending_users = {}
REMINDER_DELAY_SECONDS = 24 * 60 * 60  # 24 soat


# ==========================================
# Foydalanuvchilarni saqlash (bayram tabriklari uchun)
# ==========================================

def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def save_user(chat_id):
    users = load_users()
    if chat_id not in users:
        users.add(chat_id)
        with open(USERS_FILE, "w") as f:
            json.dump(list(users), f)


def send_sticker_safe(chat_id, sticker_key):
    """Stikerni xavfsiz yuboradi, xato bo'lsa botni to'xtatmaydi."""
    sticker_id = STICKERS.get(sticker_key)
    if sticker_id:
        try:
            bot.send_sticker(chat_id, sticker_id)
        except Exception as e:
            print(f"Stiker yuborishda xatolik ({sticker_key}): {e}")


# ==========================================
# /start — asosiy menyu
# ==========================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    # Foydalanuvchini ro'yxatga olamiz (bayram tabriklari uchun)
    save_user(message.chat.id)

    # Avval dumaloq (video note) tanishtiruv videosini yuboramiz
    try:
        with open(WELCOME_VIDEO_NOTE, "rb") as video:
            bot.send_video_note(message.chat.id, video)
    except FileNotFoundError:
        pass  # Video fayl topilmasa, shunchaki o'tkazib yuboramiz

    # Xush kelibsiz stikeri
    send_sticker_safe(message.chat.id, "welcome")

    text = (
        "🦅 <b>DELTA TOUR PREMIUM</b>\n\n"
        "Assalomu alaykum, hurmatli turist!\n\n"
        "Delta Tour Premium kanaliga xush kelibsiz.\n\n"
        "Har bir sayohat — bizning tajribamiz, sizning ishonchingiz bilan boshlanadi.\n\n"
        "👥 10 000+ mijozimiz allaqachon unutilmas sayohatga chiqdi, shundan 500+ "
        "mijozimiz shengen vizasini muvaffaqiyatli qo'lga kiritdi ✅\n\n"
        "Bu kanalda sizni nimalar kutmoqda:\n\n"
        "💎 Eksklyuziv, hamyonbop narxlardagi turlar\n"
        "💰 Har bir turda kafolatlangan tejamkorlik — 100$dan minglab dollargacha\n"
        "🛂 Shengen viza xizmatlarida <b>70% chegirma</b> va professional yordam\n"
        "🎁 Har bir tarifda sizni kutayotgan noyob sovg'alar\n\n"
        "Hoziroq obuna bo'lib, birinchilardan bo'lib ushbu imkoniyatlarga ega bo'ling.\n\n"
        "⏳ Joylar cheklangan — o'zingizga mos tarifni tanlang 👇"
    )
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, t in TARIFFS.items():
        markup.add(
            types.InlineKeyboardButton(
                f"{t['name']} — {t['price']}", callback_data=f"tariff_{key}"
            )
        )
    markup.add(types.InlineKeyboardButton("ℹ️ Barcha tariflar haqida", callback_data="all_info"))
    markup.add(
        types.InlineKeyboardButton("📍 Manzil", callback_data="show_location"),
        types.InlineKeyboardButton("🏢 Biz haqimizda", callback_data="show_about"),
    )
    bot.send_message(message.chat.id, text, parse_mode="HTML", reply_markup=markup)


# ==========================================
# Barcha tariflarni bitta xabarda ko'rsatish
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "all_info")
def show_all(call):
    text = "📋 <b>Barcha tariflar:</b>\n\n"
    for t in TARIFFS.values():
        text += (
            f"<b>{t['name']}</b> — {t['price']} / {t['period']}\n"
            f"👥 {t['people']}\n"
            f"🎁 {t['gifts']}\n\n"
        )
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, t in TARIFFS.items():
        markup.add(
            types.InlineKeyboardButton(
                f"{t['name']} tanlash", callback_data=f"tariff_{key}"
            )
        )
    bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    bot.answer_callback_query(call.id)


# ==========================================
# Bitta tarifni ko'rsatish + to'lov tugmasi
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("tariff_"))
def show_tariff(call):
    key = call.data.replace("tariff_", "")
    t = TARIFFS[key]
    user_id = call.from_user.id

    # Foydalanuvchini "kutayotganlar" ro'yxatiga qo'shamiz va eslatma taymerini boshlaymiz
    pending_users[user_id] = {"tariff": key, "confirmed": False}
    threading.Thread(target=schedule_reminder, args=(user_id, key), daemon=True).start()

    # Tarifga javob sifatida "labbay" stikeri yuboramiz
    send_sticker_safe(call.message.chat.id, "labbay")

    text = (
        f"✨ <b>{t['name']} tarifi</b>\n\n"
        f"⏳ Muddat: {t['period']}\n"
        f"💰 Narx: {t['price']}\n"
        f"👥 Kimlar uchun: {t['people']}\n"
        f"🎁 Sovg'alar: {t['gifts']}\n\n"
        f"To'lovni amalga oshirish uchun pastdagi tugmani bosing.\n"
        f"To'lov qilgach, chekning skrinshotini {ADMIN_USERNAME} ga yuboring — "
        f"tekshirilgach, kanalga qo'shilish havolasi yuboriladi."
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("💳 To'lash", url=PAYMENT_LINK))
    markup.add(types.InlineKeyboardButton("✅ To'lov qildim", callback_data=f"paid_{key}"))
    markup.add(types.InlineKeyboardButton("⬅️ Orqaga", callback_data="back_to_menu"))

    bot.edit_message_text(
        text,
        chat_id=call.message.chat.id,
        message_id=call.message.message_id,
        parse_mode="HTML",
        reply_markup=markup,
    )
    bot.answer_callback_query(call.id)


# ==========================================
# "To'lov qildim" bosilganda
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid_confirmation(call):
    key = call.data.replace("paid_", "")
    tariff_name = TARIFFS[key]["name"]
    user = call.from_user

    # Foydalanuvchi to'lov qildim bosdi - eslatma yuborilmasin
    if user.id in pending_users:
        pending_users[user.id]["confirmed"] = True

    send_sticker_safe(call.message.chat.id, "thanks_for_choosing")

    text = (
        f"✅ Rahmat! <b>{tariff_name}</b> tarifi uchun to'lov haqida xabaringiz qabul qilindi.\n\n"
        f"Iltimos, to'lov chekining skrinshotini {ADMIN_USERNAME} ga shaxsan yuboring.\n"
        f"Tasdiqlangach, sizga kanalga qo'shilish havolasi yuboriladi. 🙌"
    )
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    bot.answer_callback_query(call.id, "Ma'lumot qabul qilindi!")

    # Admin sizga (agar admin ID bilsangiz) shu yerga xabar yuborish kodi qo'shilishi mumkin
    # bot.send_message(ADMIN_CHAT_ID, f"Yangi to'lov: {user.first_name} (@{user.username}) - {tariff_name}")


# ==========================================
# Manzil va "Biz haqimizda"
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "show_location")
def show_location(call):
    send_sticker_safe(call.message.chat.id, "logo")
    bot.send_location(call.message.chat.id, OFFICE_LATITUDE, OFFICE_LONGITUDE)
    try:
        with open(OFFICE_VIDEO, "rb") as video:
            bot.send_video(
                call.message.chat.id,
                video,
                caption="📍 Bizning ofisimiz manzili. Kutib qolamiz!"
            )
    except FileNotFoundError:
        pass
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "show_about")
def show_about(call):
    bot.send_message(call.message.chat.id, ABOUT_US_TEXT, parse_mode="HTML")
    bot.answer_callback_query(call.id)


# ==========================================
# Telefon raqami so'ralganda avtomatik javob
# ==========================================

PHONE_KEYWORDS = [
    "raqam", "nomer", "nomer", "telefon", "bog'lanish", "boglanish",
    "aloqa", "call", "qongiroq", "qo'ng'iroq",
]


@bot.message_handler(func=lambda message: (
    message.text
    and not message.text.startswith("/")
    and any(kw in message.text.lower() for kw in PHONE_KEYWORDS)
))
def send_phone_number(message):
    send_sticker_safe(message.chat.id, "phone")
    phones_text = "\n".join(f"📞 {p}" for p in PHONE_NUMBERS)
    text = (
        f"Bizning telefon raqamlarimiz:\n\n{phones_text}\n\n"
        f"Yoki {ADMIN_USERNAME} ga to'g'ridan-to'g'ri yozishingiz mumkin! 😊"
    )
    bot.send_message(message.chat.id, text)


# ==========================================
# Salomlashishga javob
# ==========================================

GREETING_KEYWORDS = ["salom", "assalomu", "assalom", "hello", "hi", "привет"]


@bot.message_handler(func=lambda message: (
    message.text
    and not message.text.startswith("/")
    and any(kw in message.text.lower() for kw in GREETING_KEYWORDS)
))
def reply_greeting(message):
    send_sticker_safe(message.chat.id, "va_alaykum")
    bot.send_message(message.chat.id, "Va alaykum assalom! Sizga qanday yordam bera olamiz? 😊")


# ==========================================
# Rahmatga javob
# ==========================================

THANKS_KEYWORDS = ["rahmat", "raxmat", "tashakkur", "spasibo", "thanks"]


@bot.message_handler(func=lambda message: (
    message.text
    and not message.text.startswith("/")
    and any(kw in message.text.lower() for kw in THANKS_KEYWORDS)
))
def reply_thanks(message):
    send_sticker_safe(message.chat.id, "thanks")
    bot.send_message(message.chat.id, "Arzimaydi! Doim xizmatingizdamiz 🦅")


# ==========================================
# Orqaga qaytish
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    send_welcome(call.message)
    bot.answer_callback_query(call.id)


# ==========================================
# 24 soatlik eslatma tizimi
# ==========================================

def schedule_reminder(user_id, tariff_key):
    """24 soat kutadi, agar foydalanuvchi hali to'lov qilmagan bo'lsa eslatma yuboradi."""
    time.sleep(REMINDER_DELAY_SECONDS)

    user_data = pending_users.get(user_id)
    if user_data and not user_data.get("confirmed") and user_data.get("tariff") == tariff_key:
        t = TARIFFS[tariff_key]
        text = (
            f"👋 <b>Salom!</b>\n\n"
            f"Siz kecha ✨ <b>{t['name']}</b> tarifiga qiziqish bildirgan edingiz, "
            f"lekin hali to'lovni yakunlamadingiz 🤔\n\n"
            f"💰 Narx: <b>{t['price']}</b>\n"
            f"👥 {t['people']}\n"
            f"🎁 {t['gifts']}\n\n"
            f"⏳ Joylar cheklangan — bu imkoniyatni qo'ldan boy bermang!\n"
            f"Hoziroq tarifni rasmiylashtirish uchun pastdagi tugmani bosing 👇"
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton("💳 To'lash", url=PAYMENT_LINK))
        markup.add(types.InlineKeyboardButton("✅ To'lov qildim", callback_data=f"paid_{tariff_key}"))
        send_sticker_safe(user_id, "sorry")
        try:
            bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Eslatma yuborishda xatolik ({user_id}): {e}")

        # Eslatma yuborilgach ro'yxatdan olib tashlaymiz (faqat bir marta eslatish uchun)
        pending_users.pop(user_id, None)


# ==========================================
# Bayram kunlarida avtomatik tabriklash
# ==========================================

def load_holiday_log():
    try:
        with open(HOLIDAY_LOG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_holiday_log(log):
    with open(HOLIDAY_LOG_FILE, "w") as f:
        json.dump(log, f)


def check_holidays():
    """Har soatda bir marta bugungi sana bayramga to'g'ri kelishini tekshiradi."""
    while True:
        today = datetime.date.today()
        today_key = today.strftime("%m-%d")
        year_key = str(today.year)

        if today_key in HOLIDAYS:
            log = load_holiday_log()
            already_sent = log.get(today_key) == year_key

            if not already_sent:
                text, sticker_key = HOLIDAYS[today_key]
                users = load_users()
                print(f"Bayram tabrigi yuborilmoqda: {today_key} -> {len(users)} foydalanuvchiga")
                for chat_id in users:
                    try:
                        send_sticker_safe(chat_id, sticker_key)
                        bot.send_message(chat_id, text, parse_mode="HTML")
                        time.sleep(0.1)  # Telegram limitlariga hurmat
                    except Exception as e:
                        print(f"Tabrik yuborishda xatolik ({chat_id}): {e}")

                log[today_key] = year_key
                save_holiday_log(log)

        time.sleep(3600)  # Har soatda tekshiramiz


# ==========================================
# Admin uchun: tasdiqlangach kanalga link yuborish
# Foydalanish: admin botga shaxsan /approve @username deb yozadi
# ==========================================

@bot.message_handler(commands=["approve"])
def approve_user(message):
    # Faqat siz (admin) ishlatishingiz uchun oddiy himoya:
    # agar xohlasangiz, bu yerga o'z Telegram user ID'ingizni yozib tekshirish qo'shishingiz mumkin
    try:
        target_username = message.text.split()[1]
        bot.reply_to(
            message,
            f"{target_username} uchun kanal havolasi tayyorlandi:\n{CHANNEL_INVITE_LINK}\n\n"
            f"Buni mijozga qo'lda yuboring (hozircha avtomatik yuborish yo'q)."
        )
    except IndexError:
        bot.reply_to(message, "Foydalanish: /approve @username")


# ==========================================
# Botni ishga tushirish
# ==========================================

app = Flask(__name__)


@app.route("/")
def home():
    # Render.com botni "tirik" deb bilishi uchun oddiy sahifa
    return "Delta Tour Premium bot ishlamoqda!"


def run_bot():
    print("Bot ishga tushdi...")
    bot.infinity_polling()


if __name__ == "__main__":
    # Botni alohida oqim (thread)da ishga tushiramiz
    threading.Thread(target=run_bot).start()

    # Bayram tabriklarini tekshiruvchi oqim
    threading.Thread(target=check_holidays, daemon=True).start()

    # Flask serverni Render bergan portda ishga tushiramiz
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
