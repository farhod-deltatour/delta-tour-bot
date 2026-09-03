# -*- coding: utf-8 -*-
"""
Delta Tour Premium — Telegram bot (O'zbek / Rus tillarida)
Yopiq kanal uchun tarif tanlash va to'lov havolasini yuboruvchi bot.

ISHGA TUSHIRISH:
1. pip install pyTelegramBotAPI flask
2. Pastdagi BOT_TOKEN, ADMIN_USERNAME, PAYMENT_LINK qiymatlarini o'zgartiring
3. python delta_tour_bot.py

MUHIM: Taklif/shikoyatlarni admin'ga yo'naltirish uchun ADMIN_CHAT_ID kerak.
Buni olish uchun: botni ishga tushiring, o'zingiz botga /myid deb yozing,
bot qaytargan raqamni pastdagi ADMIN_CHAT_ID ga qo'ying, qayta deploy qiling.
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

# Taklif/shikoyatlarni yuborish uchun sizning shaxsiy chat ID'ingiz.
# /myid buyrug'i orqali oling va shu yerga qo'ying (raqam, tirnoqsiz).
ADMIN_CHAT_ID = 5103323070

# Click/Payme to'lov sahifangiz havolasi
PAYMENT_LINK = "https://payme.uz/fallback/merchant/?id=6981e2d99949957019e20311"

# Kanal invite linklari
CHANNEL_INVITE_LINK = "https://t.me/+b3wNF7hhzvliZDUy"   # Pullik Premium kanal
FREE_CHANNEL_LINK = "https://t.me/deltatouruz"            # Bepul kanal

# /start bosilganda yuboriladigan dumaloq (video note) tanishtiruv videosi.
WELCOME_VIDEO_NOTE = "welcome.mp4"

# Telefon raqamlar
PHONE_NUMBERS = ["+998 90 823 90 00", "+998 90 814 90 00"]

# Ofis joylashuvi (Google Maps koordinatalari)
OFFICE_LATITUDE = 41.363040428422835
OFFICE_LONGITUDE = 69.2754007070276

# Manzil rasmi
OFFICE_PHOTO = "office_photo.jpg"

# Litsenziya hujjatlari (PDF)
LICENSE_DOCS = ["docs/guvohnoma.pdf", "docs/litsenziya.pdf"]

# Foydalanuvchilar ro'yxati saqlanadigan fayl (bayram tabriklari uchun)
USERS_FILE = "bot_users.json"
# Qaysi bayram qaysi yilda yuborilganini saqlash uchun fayl
HOLIDAY_LOG_FILE = "holiday_log.json"
# Foydalanuvchi tanlagan til saqlanadigan fayl
LANG_FILE = "user_lang.json"
DEFAULT_LANG = "uz"

# ==========================================
# STIKERLAR — turli holatlar uchun
# ==========================================

STICKERS = {
    "welcome": "CAACAgIAAxkBAAMVaphWMNhWdNoPCmrPZN0TLFokWv0AAphfAAJ_f6BIFLmS5SAPVpY9BA",
    "va_alaykum": "CAACAgIAAxkBAAMraphd6TEI-oHGjLFwrom9Th5_2uQAAulkAAIbQ5hIFf4B0VZddsY9BA",
    "logo": "CAACAgIAAxkBAAM5aphefS4TWBBUK1u7tNCWBbFqR9wAAkpiAAK5MqFINeXuV-cjHCo9BA",
    "thanks": "CAACAgIAAxkBAAMWaphWOBWIcsQ4QrG5JDZWft06xXkAAoVrAAIUlKFIel6jfB7bAAFsPQQ",
    "thanks_for_choosing": "CAACAgIAAxkBAAM7aphejsxNbq3Znc9Vt4dXZNQiwecAAr5oAAIrYslIuBB-rOIIE9U9BA",
    "holiday": "CAACAgIAAxkBAAMzapheOkH7FpbuJI0GguDh4rXapAYAAstiAAJZv6FIse5EY2-k1BM9BA",
    "qurbon_hayit": "CAACAgIAAxkBAAMxapheIbJ2WZfNAgiAUlMmmVReXMUAAvBtAAI956FIZuzDgJjY9xk9BA",
    "sorry": "CAACAgIAAxkBAAMvapheEphkSO-8rOVwkBLiSIwUqYkAAqdgAAJUC6hIOGW2PX2pgPY9BA",
    "phone": "CAACAgIAAxkBAAMtaphd--zLu8HRsSnEE7OypsYpeF0AAsBiAAKph6lIu6WR5l0NNWo9BA",
    "labbay": "CAACAgIAAxkBAAM1apheU-wOB9DYcby2q1lZrvvZybMAAvtnAAJxvqFIiMIHOtI1xVg9BA",
}

# ==========================================
# TARIFLAR (ikki tilda)
# ==========================================

TARIFFS = {
    "uz": {
        "standard": {"name": "STANDART", "period": "1 oyga (1 martalik to'lov)", "price": "atigi 150 000 so'm",
                      "people": "Siz va +1 kishigacha (Chegirma amal qiladi)", "gifts": "—"},
        "premium": {"name": "PREMIUM", "period": "3 oyga (1 martalik to'lov)", "price": "atigi 600 000 so'm",
                     "people": "Siz va +4 kishigacha (Chegirma amal qiladi)", "gifts": "Yostiqcha + esdalik sovg'a"},
        "vip": {"name": "VIP", "period": "6 oyga (1 martalik to'lov)", "price": "2 300 000 so'm",
                "people": "10 kishigacha sovg'a qilish imkoni (Chegirma amal qiladi)", "gifts": "Esm + yostiqcha + maxsus esdalik + ryukzak"},
    },
    "ru": {
        "standard": {"name": "СТАНДАРТ", "period": "1 месяц (единоразово)", "price": "всего 150 000 сум",
                      "people": "Вы и +1 человек (Скидка действует)", "gifts": "—"},
        "premium": {"name": "ПРЕМИУМ", "period": "3 месяца (единоразово)", "price": "всего 600 000 сум",
                     "people": "Вы и +4 человека (Скидка действует)", "gifts": "Подушка + памятный подарок"},
        "vip": {"name": "VIP", "period": "6 месяцев (единоразово)", "price": "2 300 000 сум",
                "people": "Возможность подарить до 10 человек (Скидка действует)", "gifts": "Кепка + подушка + особый подарок + рюкзак"},
    },
}

# ==========================================
# UMUMIY MATNLAR (ikki tilda)
# ==========================================

TEXTS = {
    "uz": {
        "choose_language": "🌐 Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        "welcome": (
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
        ),
        "menu_hint": "Pastdagi menyudan kerakli bo'limni tanlashingiz mumkin 👇",
        "all_tariffs_title": "📋 <b>Barcha tariflar:</b>\n\n",
        "tariffs_note": (
            "\n⚠️ <b>Eslatma:</b> Barcha chegirmalardan faqat pullik obuna aktiv "
            "vaqtida foydalanishingiz mumkin! Obuna muddati tugashidan oldin "
            "to'lovni amalga oshirishingizni so'raymiz.\n\n"
            "Ushbu eksklyuziv kanaldagi xizmatlardan turli xil ko'rinishdagi "
            "vaucher va sertifikatlardan foydalanib bo'lmaydi — lekin bizning "
            "boshqa kanalimizdagi (masalan: https://t.me/deltatouruz) turlar "
            "uchun ulardan to'liq foydalanishingiz mumkin."
        ),
        "select_tariff_btn": "{name} tanlash",
        "all_info_btn": "ℹ️ Barcha tariflar haqida",
        "pay_btn": "💳 To'lash",
        "paid_btn": "✅ To'lov qildim",
        "back_btn": "⬅️ Orqaga",
        "tariff_detail": (
            "✨ <b>{name} tarifi</b>\n\n"
            "⏳ Muddat: {period}\n"
            "💰 Narx: {price}\n"
            "👥 Kimlar uchun: {people}\n"
            "🎁 Sovg'alar: {gifts}\n\n"
            "To'lovni amalga oshirish uchun pastdagi tugmani bosing.\n"
            "To'lov qilgach, chekning skrinshotini {admin} ga yuboring — "
            "tekshirilgach, kanalga qo'shilish havolasi yuboriladi."
        ),
        "paid_confirmation": (
            "✅ Rahmat! <b>{name}</b> tarifi uchun to'lov haqida xabaringiz qabul qilindi.\n\n"
            "Iltimos, to'lov chekining skrinshotini {admin} ga shaxsan yuboring.\n"
            "Tasdiqlangach, sizga kanalga qo'shilish havolasi yuboriladi. 🙌"
        ),
        "paid_answer": "Ma'lumot qabul qilindi!",
        "reminder": (
            "👋 <b>Salom!</b>\n\n"
            "Siz kecha ✨ <b>{name}</b> tarifiga qiziqish bildirgan edingiz, "
            "lekin hali to'lovni yakunlamadingiz 🤔\n\n"
            "💰 Narx: <b>{price}</b>\n"
            "👥 {people}\n"
            "🎁 {gifts}\n\n"
            "⏳ Joylar cheklangan — bu imkoniyatni qo'ldan boy bermang!\n"
            "Hoziroq tarifni rasmiylashtirish uchun pastdagi tugmani bosing 👇"
        ),
        "about_us": (
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
        ),
        "location_caption": "📍 Bizning ofisimiz manzili. Kutib qolamiz!",
        "phone_reply": "👤 <b>Menejer bilan bog'lanish:</b>\n\nTelegram: {admin}\n{phones}",
        "greeting_reply": "Va alaykum assalom! Sizga qanday yordam bera olamiz? 😊",
        "thanks_reply": "Arzimaydi! Doim xizmatingizdamiz 🦅",
        # Pastki (doimiy) menyu tugmalari
        "menu_tariffs": "🎫 Obuna bo'lish",
        "menu_manager": "💬 Menejer bilan aloqa",
        "menu_info": "ℹ️ Ma'lumot",
        "menu_location": "📍 Manzil",
        "menu_free_channel": "🎁 Bepul kanal",
        "menu_premium_channel": "💎 Premium kanal",
        "menu_complaint": "📝 Taklif va shikoyatlar",
        # "Ma'lumot" ichki bo'limi
        "info_about_btn": "🏢 Biz haqimizda",
        "info_license_btn": "📜 Litsenziya",
        "license_caption": "📜 Delta Tour rasmiy hujjatlari",
        # Kanal tugmalari
        "free_channel_text": "🆓 Bizning bepul kanalimizga xush kelibsiz!",
        "free_channel_btn": "Kanalga o'tish",
        "premium_channel_text": "💎 Bu — yopiq Premium kanal. A'zo bo'lish uchun quyidagi havolani bosing (to'lov tasdiqlangach kirish huquqi beriladi).",
        "premium_channel_btn": "Kanalga o'tish",
        # Taklif va shikoyatlar
        "complaint_prompt": "📝 Fikringiz biz uchun muhim! Taklif yoki shikoyatingizni shu yerga yozing — albatta ko'rib chiqamiz.",
        "complaint_thanks": "✅ Rahmat! Xabaringiz qabul qilindi, tez orada ko'rib chiqamiz.",
    },
    "ru": {
        "choose_language": "🌐 Iltimos, tilni tanlang / Пожалуйста, выберите язык:",
        "welcome": (
            "🦅 <b>DELTA TOUR PREMIUM</b>\n\n"
            "Здравствуйте, уважаемый турист!\n\n"
            "Добро пожаловать в Delta Tour Premium.\n\n"
            "Каждое путешествие начинается с нашего опыта и вашего доверия.\n\n"
            "👥 Более 10 000 наших клиентов уже отправились в незабываемое путешествие, "
            "из них 500+ клиентов успешно получили шенгенскую визу ✅\n\n"
            "Что вас ждёт в этом канале:\n\n"
            "💎 Эксклюзивные туры по доступным ценам\n"
            "💰 Гарантированная экономия в каждом туре — от 100$ до нескольких тысяч долларов\n"
            "🛂 Скидка <b>70%</b> на услуги шенгенской визы и профессиональная помощь\n"
            "🎁 Уникальные подарки в каждом тарифе\n\n"
            "Подпишитесь прямо сейчас и одним из первых получите эти возможности.\n\n"
            "⏳ Места ограничены — выберите подходящий тариф 👇"
        ),
        "menu_hint": "Вы можете выбрать нужный раздел в меню ниже 👇",
        "all_tariffs_title": "📋 <b>Все тарифы:</b>\n\n",
        "tariffs_note": (
            "\n⚠️ <b>Примечание:</b> Все скидки действуют только во время активной "
            "платной подписки! Просим вас произвести оплату до истечения срока "
            "подписки.\n\n"
            "Различные ваучеры и сертификаты нельзя использовать на услуги этого "
            "эксклюзивного канала — но для туров в нашем другом канале "
            "(например: https://t.me/deltatouruz) вы можете использовать их "
            "в полной мере."
        ),
        "select_tariff_btn": "Выбрать {name}",
        "all_info_btn": "ℹ️ Обо всех тарифах",
        "pay_btn": "💳 Оплатить",
        "paid_btn": "✅ Я оплатил(а)",
        "back_btn": "⬅️ Назад",
        "tariff_detail": (
            "✨ <b>Тариф {name}</b>\n\n"
            "⏳ Срок: {period}\n"
            "💰 Цена: {price}\n"
            "👥 Для кого: {people}\n"
            "🎁 Подарки: {gifts}\n\n"
            "Для оплаты нажмите кнопку ниже.\n"
            "После оплаты отправьте скриншот чека {admin} — "
            "после проверки вам будет отправлена ссылка на вступление в канал."
        ),
        "paid_confirmation": (
            "✅ Спасибо! Информация об оплате тарифа <b>{name}</b> принята.\n\n"
            "Пожалуйста, отправьте скриншот чека лично {admin}.\n"
            "После подтверждения вам будет отправлена ссылка на вступление в канал. 🙌"
        ),
        "paid_answer": "Информация принята!",
        "reminder": (
            "👋 <b>Здравствуйте!</b>\n\n"
            "Вчера вы интересовались тарифом ✨ <b>{name}</b>, но ещё не завершили оплату 🤔\n\n"
            "💰 Цена: <b>{price}</b>\n"
            "👥 {people}\n"
            "🎁 {gifts}\n\n"
            "⏳ Места ограничены — не упустите эту возможность!\n"
            "Нажмите кнопку ниже, чтобы оформить тариф прямо сейчас 👇"
        ),
        "about_us": (
            "🦅 <b>Delta Tour</b> — работаем для вас с 2021 года, более 5 лет опыта.\n\n"
            "🏆 2023 год — лидер продаж по направлению Шарм-эль-Шейх\n"
            "🏆 2024-2025 годы — лидер продаж по направлению Турция\n\n"
            "Мы организуем туры по направлениям Турция, Шарм-эль-Шейх, Вьетнам, "
            "Таиланд, Бали, Куала-Лумпур, Грузия и Азербайджан. Кроме того, "
            "занимаемся индивидуальными и экскурсионными турами в любой город мира, "
            "а также групповыми и корпоративными поездками.\n\n"
            "Каждое путешествие начинается с нашего опыта и вашего доверия.\n\n"
            "👥 Более 10 000 наших клиентов уже отправились в незабываемое путешествие, "
            "из них 500+ клиентов успешно получили шенгенскую визу ✅"
        ),
        "location_caption": "📍 Адрес нашего офиса. Ждём вас!",
        "phone_reply": "👤 <b>Связь с менеджером:</b>\n\nTelegram: {admin}\n{phones}",
        "greeting_reply": "И вам здравствуйте! Чем можем помочь? 😊",
        "thanks_reply": "Не за что! Всегда к вашим услугам 🦅",
        "menu_tariffs": "🎫 Оформить подписку",
        "menu_manager": "💬 Связь с менеджером",
        "menu_info": "ℹ️ Информация",
        "menu_location": "📍 Адрес",
        "menu_free_channel": "🎁 Бесплатный канал",
        "menu_premium_channel": "💎 Премиум канал",
        "menu_complaint": "📝 Предложения и жалобы",
        "info_about_btn": "🏢 О нас",
        "info_license_btn": "📜 Лицензия",
        "license_caption": "📜 Официальные документы Delta Tour",
        "free_channel_text": "🆓 Добро пожаловать в наш бесплатный канал!",
        "free_channel_btn": "Перейти в канал",
        "premium_channel_text": "💎 Это закрытый Premium канал. Для вступления нажмите на ссылку ниже (доступ открывается после подтверждения оплаты).",
        "premium_channel_btn": "Перейти в канал",
        "complaint_prompt": "📝 Ваше мнение важно для нас! Напишите ваше предложение или жалобу — мы обязательно рассмотрим её.",
        "complaint_thanks": "✅ Спасибо! Ваше сообщение принято, мы скоро его рассмотрим.",
    },
}

# ==========================================
# BAYRAMLAR — avtomatik tabriklash (ikki tilda)
# ==========================================

HOLIDAYS = {
    "01-01": {
        "uz": ("🎉 <b>Yangi yil bilan tabriklaymiz!</b>\n\n"
               "Delta Tour jamoasi sizga yangi yilda yangi manzillar, unutilmas "
               "sayohatlar va baxtli lahzalar tilaydi! 🥂✈️"),
        "ru": ("🎉 <b>С Новым годом!</b>\n\n"
               "Команда Delta Tour желает вам новых направлений, незабываемых "
               "путешествий и счастливых моментов в новом году! 🥂✈️"),
        "sticker": "holiday",
    },
    "03-21": {
        "uz": ("🌸 <b>Navro'z bayrami muborak bo'lsin!</b>\n\n"
               "Yangi bahor, yangi umidlar va yangi sayohatlar bilan! "
               "Delta Tour jamoasidan issiq tabriklar. 🌿"),
        "ru": ("🌸 <b>С праздником Навруз!</b>\n\n"
               "С новой весной, новыми надеждами и новыми путешествиями! "
               "Тёплые поздравления от команды Delta Tour. 🌿"),
        "sticker": "holiday",
    },
    "09-01": {
        "uz": ("🇺🇿 <b>Mustaqillik kuningiz muborak bo'lsin!</b>\n\n"
               "Delta Tour jamoasi sizni mamlakatimiz mustaqilligi bayrami bilan "
               "tabriklaydi! 🎊"),
        "ru": ("🇺🇿 <b>С Днём независимости!</b>\n\n"
               "Команда Delta Tour поздравляет вас с праздником независимости "
               "нашей страны! 🎊"),
        "sticker": "holiday",
    },
    # ⚠️ MUHIM: Qurbon hayiti sanasi har yili o'zgaradi (hijriy taqvim bo'yicha).
    "06-17": {
        "uz": ("🕌 <b>Qurbon hayiti muborak bo'lsin!</b>\n\n"
               "Delta Tour jamoasi sizni muqaddas Qurbon hayiti bayrami bilan "
               "tabriklaydi! Uy-joyingizga tinchlik, oilangizga baraka tilaymiz."),
        "ru": ("🕌 <b>С праздником Курбан-байрам!</b>\n\n"
               "Команда Delta Tour поздравляет вас со священным праздником "
               "Курбан-байрам! Желаем мира вашему дому и благополучия вашей семье."),
        "sticker": "qurbon_hayit",
    },
}

bot = telebot.TeleBot(BOT_TOKEN)

pending_users = {}
REMINDER_DELAY_SECONDS = 24 * 60 * 60  # 24 soat

# Taklif/shikoyat kutilayotgan foydalanuvchilar (chat_id to'plami)
awaiting_complaint = set()


# ==========================================
# Foydalanuvchilarni saqlash
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
    sticker_id = STICKERS.get(sticker_key)
    if sticker_id:
        try:
            bot.send_sticker(chat_id, sticker_id)
        except Exception as e:
            print(f"Stiker yuborishda xatolik ({sticker_key}): {e}")


# ==========================================
# Til bilan ishlash
# ==========================================

def load_langs():
    try:
        with open(LANG_FILE, "r") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_lang(chat_id, lang):
    langs = load_langs()
    langs[str(chat_id)] = lang
    with open(LANG_FILE, "w") as f:
        json.dump(langs, f)


def get_lang(chat_id):
    langs = load_langs()
    return langs.get(str(chat_id))


# ==========================================
# Pastki (doimiy) menyu klaviaturasi
# ==========================================

def get_main_reply_keyboard(lang):
    t = TEXTS[lang]
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        types.KeyboardButton(t["menu_tariffs"]),
        types.KeyboardButton(t["menu_manager"]),
    )
    markup.add(
        types.KeyboardButton(t["menu_info"]),
        types.KeyboardButton(t["menu_location"]),
    )
    markup.add(
        types.KeyboardButton(t["menu_free_channel"]),
        types.KeyboardButton(t["menu_premium_channel"]),
    )
    markup.add(types.KeyboardButton(t["menu_complaint"]))
    return markup


def get_menu_action_map():
    """Matn -> (action, lang) lug'atini quradi, ikkala til uchun ham."""
    mapping = {}
    actions = [
        "menu_tariffs", "menu_manager", "menu_info", "menu_location",
        "menu_free_channel", "menu_premium_channel", "menu_complaint",
    ]
    for lang in ("uz", "ru"):
        for action in actions:
            label = TEXTS[lang][action]
            mapping[label] = (action, lang)
    return mapping


# ==========================================
# Asosiy menyuni yuborish (til tanlangandan keyin)
# ==========================================

def send_main_menu(chat_id, lang):
    t = TEXTS[lang]

    try:
        with open(WELCOME_VIDEO_NOTE, "rb") as video:
            bot.send_video_note(chat_id, video)
    except FileNotFoundError:
        pass

    send_sticker_safe(chat_id, "welcome")

    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, tariff in TARIFFS[lang].items():
        markup.add(
            types.InlineKeyboardButton(
                f"{tariff['name']} — {tariff['price']}", callback_data=f"tariff_{key}"
            )
        )
    markup.add(types.InlineKeyboardButton(t["all_info_btn"], callback_data="all_info"))
    bot.send_message(chat_id, t["welcome"], parse_mode="HTML", reply_markup=markup)

    # Pastki doimiy menyu
    bot.send_message(chat_id, t["menu_hint"], reply_markup=get_main_reply_keyboard(lang))


# ==========================================
# /start — til tanlash yoki asosiy menyu
# ==========================================

@bot.message_handler(commands=["start"])
def send_welcome(message):
    save_user(message.chat.id)
    lang = get_lang(message.chat.id)

    if lang is None:
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🇺🇿 O'zbekcha", callback_data="setlang_uz"),
            types.InlineKeyboardButton("🇷🇺 Русский", callback_data="setlang_ru"),
        )
        bot.send_message(
            message.chat.id,
            TEXTS["uz"]["choose_language"],
            reply_markup=markup,
        )
    else:
        send_main_menu(message.chat.id, lang)


@bot.message_handler(commands=["myid"])
def myid(message):
    bot.reply_to(message, f"Sizning chat ID: <code>{message.chat.id}</code>", parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data.startswith("setlang_"))
def set_language(call):
    lang = call.data.replace("setlang_", "")
    save_lang(call.message.chat.id, lang)
    bot.answer_callback_query(call.id)
    send_main_menu(call.message.chat.id, lang)


# ==========================================
# Barcha tariflarni bitta xabarda ko'rsatish
# ==========================================

def send_tariffs_overview(chat_id, lang):
    t = TEXTS[lang]
    text = t["all_tariffs_title"]
    for tariff in TARIFFS[lang].values():
        text += (
            f"<b>{tariff['name']}</b> — {tariff['price']} / {tariff['period']}\n"
            f"👥 {tariff['people']}\n"
            f"🎁 {tariff['gifts']}\n\n"
        )
    text += t["tariffs_note"]
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, tariff in TARIFFS[lang].items():
        markup.add(
            types.InlineKeyboardButton(
                t["select_tariff_btn"].format(name=tariff["name"]), callback_data=f"tariff_{key}"
            )
        )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=markup, disable_web_page_preview=True)


@bot.callback_query_handler(func=lambda call: call.data == "all_info")
def show_all(call):
    lang = get_lang(call.message.chat.id) or DEFAULT_LANG
    send_tariffs_overview(call.message.chat.id, lang)
    bot.answer_callback_query(call.id)


# ==========================================
# Bitta tarifni ko'rsatish + to'lov tugmasi
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("tariff_"))
def show_tariff(call):
    key = call.data.replace("tariff_", "")
    lang = get_lang(call.message.chat.id) or DEFAULT_LANG
    t = TEXTS[lang]
    tariff = TARIFFS[lang][key]
    user_id = call.from_user.id

    pending_users[user_id] = {"tariff": key, "confirmed": False, "lang": lang}
    threading.Thread(target=schedule_reminder, args=(user_id, key), daemon=True).start()

    text = t["tariff_detail"].format(
        name=tariff["name"], period=tariff["period"], price=tariff["price"],
        people=tariff["people"], gifts=tariff["gifts"], admin=ADMIN_USERNAME,
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t["pay_btn"], url=PAYMENT_LINK))
    markup.add(types.InlineKeyboardButton(t["paid_btn"], callback_data=f"paid_{key}"))
    markup.add(types.InlineKeyboardButton(t["back_btn"], callback_data="back_to_menu"))

    try:
        bot.edit_message_text(
            text,
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            parse_mode="HTML",
            reply_markup=markup,
        )
    except Exception:
        bot.send_message(call.message.chat.id, text, parse_mode="HTML", reply_markup=markup)
    bot.answer_callback_query(call.id)


# ==========================================
# "To'lov qildim" bosilganda
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data.startswith("paid_"))
def paid_confirmation(call):
    key = call.data.replace("paid_", "")
    lang = get_lang(call.message.chat.id) or DEFAULT_LANG
    t = TEXTS[lang]
    tariff_name = TARIFFS[lang][key]["name"]
    user = call.from_user

    if user.id in pending_users:
        pending_users[user.id]["confirmed"] = True

    send_sticker_safe(call.message.chat.id, "thanks_for_choosing")

    text = t["paid_confirmation"].format(name=tariff_name, admin=ADMIN_USERNAME)
    bot.send_message(call.message.chat.id, text, parse_mode="HTML")
    bot.answer_callback_query(call.id, t["paid_answer"])


# ==========================================
# Manzil, Ma'lumot (Biz haqimizda / Litsenziya)
# ==========================================

def send_location(chat_id, lang):
    send_sticker_safe(chat_id, "logo")
    bot.send_location(chat_id, OFFICE_LATITUDE, OFFICE_LONGITUDE)
    try:
        with open(OFFICE_PHOTO, "rb") as photo:
            bot.send_photo(chat_id, photo, caption=TEXTS[lang]["location_caption"])
    except FileNotFoundError:
        pass


def send_info_menu(chat_id, lang):
    t = TEXTS[lang]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t["info_about_btn"], callback_data="info_about"))
    markup.add(types.InlineKeyboardButton(t["info_license_btn"], callback_data="info_license"))
    bot.send_message(chat_id, t["menu_info"], reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "info_about")
def info_about(call):
    lang = get_lang(call.message.chat.id) or DEFAULT_LANG
    bot.send_message(call.message.chat.id, TEXTS[lang]["about_us"], parse_mode="HTML")
    bot.answer_callback_query(call.id)


@bot.callback_query_handler(func=lambda call: call.data == "info_license")
def info_license(call):
    lang = get_lang(call.message.chat.id) or DEFAULT_LANG
    for doc_path in LICENSE_DOCS:
        try:
            with open(doc_path, "rb") as doc:
                bot.send_document(call.message.chat.id, doc)
        except FileNotFoundError:
            print(f"Hujjat topilmadi: {doc_path}")
    bot.answer_callback_query(call.id)


# ==========================================
# Kanal tugmalari
# ==========================================

def send_free_channel(chat_id, lang):
    t = TEXTS[lang]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t["free_channel_btn"], url=FREE_CHANNEL_LINK))
    bot.send_message(chat_id, t["free_channel_text"], reply_markup=markup)


def send_premium_channel(chat_id, lang):
    t = TEXTS[lang]
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton(t["premium_channel_btn"], url=CHANNEL_INVITE_LINK))
    bot.send_message(chat_id, t["premium_channel_text"], reply_markup=markup)


# ==========================================
# Menejer bilan bog'lanish (telefon)
# ==========================================

def send_manager_contact(chat_id, lang):
    send_sticker_safe(chat_id, "phone")
    phone_label = "Telefon" if lang == "uz" else "Телефон"
    phones_text = "\n".join(f"{phone_label}: {p}" for p in PHONE_NUMBERS)
    text = TEXTS[lang]["phone_reply"].format(phones=phones_text, admin=ADMIN_USERNAME)
    bot.send_message(chat_id, text, parse_mode="HTML")


# ==========================================
# Taklif va shikoyatlar
# ==========================================

def start_complaint(chat_id, lang):
    awaiting_complaint.add(chat_id)
    bot.send_message(chat_id, TEXTS[lang]["complaint_prompt"])


def forward_complaint(message, lang):
    awaiting_complaint.discard(message.chat.id)
    user = message.from_user
    if ADMIN_CHAT_ID:
        try:
            username_part = f"@{user.username}" if user.username else "username yo'q"
            info = f"📝 Yangi murojaat:\n{user.first_name} ({username_part}, id: {user.id})\n\n{message.text}"
            bot.send_message(ADMIN_CHAT_ID, info)
        except Exception as e:
            print(f"Murojaatni yuborishda xatolik: {e}")
    else:
        print(f"ADMIN_CHAT_ID sozlanmagan! Murojaat: {message.text}")
    bot.send_message(message.chat.id, TEXTS[lang]["complaint_thanks"])


# ==========================================
# Orqaga qaytish
# ==========================================

@bot.callback_query_handler(func=lambda call: call.data == "back_to_menu")
def back_to_menu(call):
    lang = get_lang(call.message.chat.id) or DEFAULT_LANG
    bot.answer_callback_query(call.id)
    send_tariffs_overview(call.message.chat.id, lang)


# ==========================================
# BARCHA MATNLI XABARLARNI BOSHQARISH
# (menyu tugmalari, taklif/shikoyat, salom, rahmat, telefon so'rovi)
# ==========================================

PHONE_KEYWORDS = [
    "raqam", "nomer", "telefon", "bog'lanish", "boglanish",
    "aloqa", "call", "qongiroq", "qo'ng'iroq",
    "номер", "телефон", "связь", "звонок",
]
GREETING_KEYWORDS = ["salom", "assalomu", "assalom", "hello", "hi", "привет", "здравств"]
THANKS_KEYWORDS = ["rahmat", "raxmat", "tashakkur", "spasibo", "thanks", "спасибо", "благодар"]

MENU_ACTION_MAP = get_menu_action_map()


@bot.message_handler(func=lambda message: message.text and not message.text.startswith("/"))
def handle_text(message):
    chat_id = message.chat.id
    text = message.text
    lang = get_lang(chat_id) or DEFAULT_LANG

    # 1) Pastki menyu tugmalaridan biri bosilganmi?
    if text in MENU_ACTION_MAP:
        action, btn_lang = MENU_ACTION_MAP[text]
        lang = btn_lang  # tugma matni qaysi tilga tegishli bo'lsa, o'shani ishlatamiz
        if action == "menu_tariffs":
            send_tariffs_overview(chat_id, lang)
        elif action == "menu_manager":
            send_manager_contact(chat_id, lang)
        elif action == "menu_info":
            send_info_menu(chat_id, lang)
        elif action == "menu_location":
            send_location(chat_id, lang)
        elif action == "menu_free_channel":
            send_free_channel(chat_id, lang)
        elif action == "menu_premium_channel":
            send_premium_channel(chat_id, lang)
        elif action == "menu_complaint":
            start_complaint(chat_id, lang)
        return

    # 2) Taklif/shikoyat matnini kutayotgan bo'lsak - shu xabarni yo'naltiramiz
    if chat_id in awaiting_complaint:
        forward_complaint(message, lang)
        return

    # 3) Telefon so'ralganda
    if any(kw in text.lower() for kw in PHONE_KEYWORDS):
        send_manager_contact(chat_id, lang)
        return

    # 4) Salomlashish
    if any(kw in text.lower() for kw in GREETING_KEYWORDS):
        send_sticker_safe(chat_id, "va_alaykum")
        bot.send_message(chat_id, TEXTS[lang]["greeting_reply"])
        return

    # 5) Rahmat
    if any(kw in text.lower() for kw in THANKS_KEYWORDS):
        send_sticker_safe(chat_id, "thanks")
        bot.send_message(chat_id, TEXTS[lang]["thanks_reply"])
        return


# ==========================================
# 24 soatlik eslatma tizimi
# ==========================================

def schedule_reminder(user_id, tariff_key):
    time.sleep(REMINDER_DELAY_SECONDS)

    user_data = pending_users.get(user_id)
    if user_data and not user_data.get("confirmed") and user_data.get("tariff") == tariff_key:
        lang = user_data.get("lang", DEFAULT_LANG)
        t = TEXTS[lang]
        tariff = TARIFFS[lang][tariff_key]
        text = t["reminder"].format(
            name=tariff["name"], price=tariff["price"],
            people=tariff["people"], gifts=tariff["gifts"],
        )
        markup = types.InlineKeyboardMarkup(row_width=1)
        markup.add(types.InlineKeyboardButton(t["pay_btn"], url=PAYMENT_LINK))
        markup.add(types.InlineKeyboardButton(t["paid_btn"], callback_data=f"paid_{tariff_key}"))
        send_sticker_safe(user_id, "sorry")
        try:
            bot.send_message(user_id, text, parse_mode="HTML", reply_markup=markup)
        except Exception as e:
            print(f"Eslatma yuborishda xatolik ({user_id}): {e}")

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
    while True:
        today = datetime.date.today()
        today_key = today.strftime("%m-%d")
        year_key = str(today.year)

        if today_key in HOLIDAYS:
            log = load_holiday_log()
            already_sent = log.get(today_key) == year_key

            if not already_sent:
                holiday = HOLIDAYS[today_key]
                sticker_key = holiday["sticker"]
                users = load_users()
                print(f"Bayram tabrigi yuborilmoqda: {today_key} -> {len(users)} foydalanuvchiga")
                for chat_id in users:
                    try:
                        lang = get_lang(chat_id) or DEFAULT_LANG
                        text = holiday[lang]
                        send_sticker_safe(chat_id, sticker_key)
                        bot.send_message(chat_id, text, parse_mode="HTML")
                        time.sleep(0.1)
                    except Exception as e:
                        print(f"Tabrik yuborishda xatolik ({chat_id}): {e}")

                log[today_key] = year_key
                save_holiday_log(log)

        time.sleep(3600)


# ==========================================
# Admin uchun: tasdiqlangach kanalga link yuborish
# ==========================================

@bot.message_handler(commands=["approve"])
def approve_user(message):
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
    return "Delta Tour Premium bot ishlamoqda!"


def run_bot():
    print("Bot ishga tushdi...")
    bot.infinity_polling()


if __name__ == "__main__":
    threading.Thread(target=run_bot).start()
    threading.Thread(target=check_holidays, daemon=True).start()
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
