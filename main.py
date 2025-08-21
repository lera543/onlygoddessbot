# ✅ ПОЛНЫЙ РАБОЧИЙ КОД ДЛЯ ТВОЕГО БОТА OnlyGirls

import logging
import random
from datetime import datetime, timedelta
from telegram import Update, ReplyKeyboardRemove
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 👥 USERS
users = {}

# 🍆 Пиписа рост
last_grow = {}

# 🎴 Таро карты
tarot_cards = [
    ("Шут 🤡", "Новые начинания, наивность, свобода.", "Безрассудство, глупость, риски."),
    ("Маг 🧙‍♂️", "Сила воли, мастерство, проявление желаемого.", "Манипуляции, обман, неиспользованный потенциал."),
    # ... остальные карты
]

# 🪄 Предсказания (сокращённо для примера)
predictions = [
    "Сегодня тебя ждёт приятный сюрприз 💌",
    "Помни: ты достойна самого лучшего 🌟",
    "Твоя энергия — магнит для успеха ✨",
    # + ещё 197
]

# 🫂 Обнимашки
hug_phrases = [
    "💞 Обнимашки всем девочкам чата!",
    "🩷 Ты заслуживаешь тепла и любви!",
    "🌸 Объятия лечат. Вот тебе немножко!",
    "💖 Кто не обнимется — тот не играет в кастомке!",
    "🫂 Токсиков тоже иногда обнимают… по голове… табуреткой 🙃",
]

# 📜 Правила
RULES_TEXT = """
Добро пожаловать, девочка ❣️
Ознакомься с правилами клана: https://telegra.ph/Pravila-klana-ঐOnlyGirlsঐ-05-29 🫶
Важная информация — всегда в закрепе!
Клановая приставка: ঔ
"""

# ❤️‍🔥 Статусы отношений
relationships = {}

# 🔁 Старт
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет, девочка 💖 Введи /about, чтобы узнать, что я умею!")

# 👤 Профиль
async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    user = users.get(uid, {})
    text = (
        f"🙋‍♀️ Имя: {user.get('name', '')}\n"
        f"🎮 Ник в игре: `{user.get('nickname', '')}`\n"
        f"🔢 UID: `{user.get('uid', '')}`\n"
        f"🎂 Дата рождения: {user.get('bday', '')}\n"
        f"🏙 Город: {user.get('city', '')}\n"
        f"📲 ТТ или inst: {user.get('social', '')}\n"
        f"📅 Дата вступления: {user.get('joined_date', '')}\n"
        f"🍆 Пиписа: {user.get('pipisa_height', 0.0)} см\n"
        f"📝 Девиз: {user.get('quote', '')}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

# ✏️ Редактирование
async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split(maxsplit=8)[1:]
        if len(parts) != 8:
            await update.message.reply_text("Формат: /editprofile имя ник uid др город соцсеть дата цитата")
            return
        name, nickname, uid, bday, city, social, joined_date, quote = parts
        users[update.effective_user.id] = {
            "name": name,
            "nickname": nickname,
            "uid": uid,
            "bday": bday,
            "city": city,
            "social": social,
            "joined_date": joined_date,
            "quote": quote,
            "pipisa_height": users.get(update.effective_user.id, {}).get("pipisa_height", 0.0)
        }
        await update.message.reply_text("Анкета обновлена 💖")
    except Exception as e:
        logger.error(e)
        await update.message.reply_text("Ошибка при обновлении профиля")

# 🍆 Рост пиписы
async def grow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    now = datetime.now()
    if uid in last_grow and now - last_grow[uid] < timedelta(hours=24):
        await update.message.reply_text("Ты уже выращивала сегодня! Завтра ещё вырастет 🌱")
        return
    change = round(random.uniform(-10, 10), 1)
    users.setdefault(uid, {}).setdefault("pipisa_height", 0.0)
    users[uid]["pipisa_height"] = max(0.0, users[uid]["pipisa_height"] + change)
    last_grow[uid] = now
    phrase = "Пиписа выросла" if change > 0 else "Пиписа уменьшилась 😢"
    await update.message.reply_text(f"{phrase} на {abs(change)} см. Сейчас: {users[uid]['pipisa_height']} см")

# 🎴 Таро
async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card, upright, reversed = random.choice(tarot_cards)
    position = random.choice(["прямое", "перевёрнутое"])
    meaning = upright if position == "прямое" else reversed
    await update.message.reply_text(f"🔮 **{card}** ({position})\n{meaning}", parse_mode='Markdown')

# 🧠 Предсказание
async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(predictions))

# 🫂 Обнимашки
async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(hug_phrases))

# 📜 Правила
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)

# 💌 About
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("""
Я — бот клана OnlyGirls 💖 Вот что я умею:

/profile — показать анкету
/editprofile — редактировать анкету
/grow — вырастить пипису
/tarot — расклад таро
/predskaz — предсказание
/hugs — обнимашки
/rules — правила клана
/lesbi — рандомная пара из чата
""")

# 💞 Лесби пара
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(users) < 2:
        await update.message.reply_text("Недостаточно участниц для пары")
        return
    u1, u2 = random.sample(list(users.values()), 2)
    phrases = [
        "🌈 Новая пара недели!",
        "💘 Что-то между ними точно есть...",
        "👩‍❤️‍👩 Сердца бьются в унисон!",
        "🫶 Кто-то нашёл свою девочку!",
    ]
    await context.bot.send_message(chat_id=CHAT_ID, text=f"{random.choice(phrases)}\n{u1['name']} + {u2['name']} 💞")

# 🔧 Регистрируем хендлеры
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("editprofile", editprofile))
app.add_handler(CommandHandler("grow", grow))
app.add_handler(CommandHandler("tarot", tarot))
app.add_handler(CommandHandler("predskaz", predskaz))
app.add_handler(CommandHandler("hugs", hugs))
app.add_handler(CommandHandler("rules", rules))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("lesbi", lesbi))

app.run_polling()
