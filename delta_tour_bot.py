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
# /start — asosiy menyu
# ==========================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    # Avval dumaloq (video note) tanishtiruv videosini yuboramiz
    try:
        with open(WELCOME_VIDEO_NOTE, "rb") as video:
            bot.send_video_note(message.chat.id, video)
    except FileNotFoundError:
        pass  # Video fayl topilmasa, shunchaki o'tkazib yuboramiz

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
        try:
            bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Eslatma yuborishda xatolik ({user_id}): {e}")

        # Eslatma yuborilgach ro'yxatdan olib tashlaymiz (faqat bir marta eslatish uchun)
        pending_users.pop(user_id, None)


# ==========================================
# VAQTINCHALIK: Stiker ID'sini bilish uchun
# (Stiker ID'larini bilib olgach, bu qismni o'chirib tashlashingiz mumkin)
# ==========================================

@bot.message_handler(content_types=["sticker"])
def get_sticker_id(message):
    sticker_id = message.sticker.file_id
    bot.reply_to(
        message,
        f"🆔 Stiker ID:\n<code>{sticker_id}</code>\n\n"
        f"Buni nusxalab, menga (Claude'ga) yuboring.",
        parse_mode="HTML"
    )


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

    # Flask serverni Render bergan portda ishga tushiramiz
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
