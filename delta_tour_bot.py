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


# ==========================================
# /start — asosiy menyu
# ==========================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    text = (
        "🦅 <b>Delta Tour Premium</b> kanaliga xush kelibsiz!\n\n"
        "Bu yerda siz eksklyuziv turlar, shengen viza xizmatlari va "
        "maxsus takliflarga birinchilardan bo'lib ega bo'lasiz.\n\n"
        "Quyidagi tariflardan birini tanlang 👇"
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
