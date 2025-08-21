import logging
import random
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, ContextTypes,
                          MessageHandler, filters, CallbackQueryHandler, ConversationHandler)

TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

users_data = {}
married = set()
lesbi_couples = {}
last_prediction_date = {}
last_lesbi_date = None

PROFILE_QUESTIONS = [
    "Как тебя зовут? (имя)",
    "Какой у тебя ник в игре?",
    "Какой у тебя UID?",
    "Когда у тебя день рождения? (например, 01.01.2000)",
    "Из какого ты города?",
    "Оставь ссылку на свой TikTok или Instagram:",
    "Когда ты вступила в чат? (например, 01.08.2025)",
    "Поделись своим девизом или любимой цитатой:"
]

PREDICTIONS = [f"Предсказание {i}" for i in range(1, 201)]

TAROT_CARDS = [
    ("Шут 🤡", "новое начало, спонтанность, наивность", "безрассудство, неопределённость"),
    ("Маг 🧙", "воля, мастерство, творческая энергия", "манипуляции, обман, неуверенность"),
    ("Жрица 🔮", "интуиция, тайна, внутренняя мудрость", "скрытность, отстранённость")
    # Добавь остальные при желании
]

HUGS_MESSAGES = [
    "Обнимаю тебя крепко-крепко 🫂 Всё будет хорошо!",
    "Тебя кто-то обнимает прямо сейчас 🤗 Надеюсь, тебе стало теплее!",
    "Мягкие обнимашки на твой день! 🧸 Ты супер!",
    "Вот так нежно и заботливо — обнимаю 💞",
    "Кто не обнимется — тот не играет в кастомке!",
    "🫂 Токсиков тоже иногда обнимают… по голове… табуреткой 🙃"
]

PIPISA_UP_REACTIONS = [
    "Пиписа выросла как на дрожжах! 🍆✨",
    "Ого! Такая прибавка, аж в чате тепло стало 😳",
    "Пиписа тянется к солнцу! ☀️",
    "Сегодня удачный день для роста! 📈"
]

PIPISA_DOWN_REACTIONS = [
    "Упс... что-то пошло не так 😬",
    "Пиписа сжалась от холода 🥶",
    "Грустный день, даже пиписа поникла 😢",
    "Ничего, завтра вырастет снова! 💪"
]

LOVE_MESSAGES = [
    "💍 {a} и {b} теперь официально жена и жена! Поздравляем! 🎉",
    "👰‍♀️👰‍♀️ Сыграли свадьбу: {a} + {b} = 💒 Любовь!",
    "🥂 Появилась новая семейная пара: {a} & {b}! Пусть будет счастье! 🫶",
    "🎊 {a} и {b} теперь супруги в нашем клане! Нежности и обнимашек! 🥰"
]

LESBI_MESSAGES = [
    "🌈 Сегодняшняя лесби-пара: {a} и {b} 💋",
    "🫶 Кто бы мог подумать! {a} и {b} — пара дня!",
    "💘 Амур попал точно в цель! {a} и {b} теперь вместе 😍",
    "💞 Любовь витает в воздухе: {a} + {b} = ❤️"
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Я клановый бот для OnlyGirls. Напиши /about чтобы узнать, что я умею ✨")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "✨ <b>Функции бота:</b>\n"
        "/editprofile — заполнить или обновить профиль\n"
        "/profile — посмотреть профиль\n"
        "/pipisa — вырастить пипису 🍆\n"
        "/predskaz — получить предсказание\n"
        "/tarot — расклад таро\n"
        "/lesbi — случайная лесби-пара дня 🌈\n"
        "/hugs — обнимашки 🤗\n"
        "/love @user — сыграть свадьбу\n"
        "/divorce @user — развод\n"
        "/sovmestimost @user — совместимость по знакам\n"
        "/rules — правила клана 📜"
    )
    await update.message.reply_text(text, parse_mode="HTML")

# Хендлер анкеты
PROFILE, = range(1)

async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_step"] = 0
    context.user_data["profile_answers"] = []
    await update.message.reply_text(PROFILE_QUESTIONS[0])
    return PROFILE

async def profile_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    step = context.user_data["profile_step"]
    context.user_data["profile_answers"].append(update.message.text)
    step += 1
    if step >= len(PROFILE_QUESTIONS):
        users_data[update.effective_user.id] = {
            "first_name": context.user_data["profile_answers"][0],
            "nickname": context.user_data["profile_answers"][1],
            "uid": context.user_data["profile_answers"][2],
            "bday": context.user_data["profile_answers"][3],
            "city": context.user_data["profile_answers"][4],
            "social": context.user_data["profile_answers"][5],
            "joined_date": context.user_data["profile_answers"][6],
            "quote": context.user_data["profile_answers"][7],
            "pipisa_height": 0.0
        }
        await update.message.reply_text("Профиль обновлён ✅")
        return ConversationHandler.END
    else:
        context.user_data["profile_step"] = step
        await update.message.reply_text(PROFILE_QUESTIONS[step])
        return PROFILE

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = users_data.get(update.effective_user.id)
    if not user:
        await update.message.reply_text("Профиль не найден. Используй /editprofile")
        return
    text = (
        f"🙋‍♀️ Имя: {user['first_name']}\n"
        f"🎮 Ник в игре: <code>{user['nickname']}</code>\n"
        f"🔢 UID: <code>{user['uid']}</code>\n"
        f"🎂 Дата рождения: {user['bday']}\n"
        f"🏙 Город: {user['city']}\n"
        f"📲 ТТ или inst: {user['social']}\n"
        f"📅 Дата вступления: {user['joined_date']}\n"
        f"🍆 Пиписа: {user['pipisa_height']} см\n"
        f"📝 Девиз: {user['quote']}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

async def pipisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    now = datetime.datetime.now().date()
    user = users_data.get(user_id)
    if not user:
        await update.message.reply_text("Сначала заполни профиль через /editprofile")
        return
    if user.get("last_pipisa_date") == now:
        await update.message.reply_text("Сегодня ты уже растила пипису! Попробуй завтра.")
        return
    delta = round(random.uniform(-10, 10), 1)
    user["pipisa_height"] += delta
    user["pipisa_height"] = round(max(user["pipisa_height"], 0.0), 1)
    user["last_pipisa_date"] = now
    reaction = random.choice(PIPISA_UP_REACTIONS if delta > 0 else PIPISA_DOWN_REACTIONS)
    await update.message.reply_text(f"Изменение: {delta:+} см\n{reaction}")

async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    now = datetime.datetime.now().date()
    if last_prediction_date.get(uid) == now:
        await update.message.reply_text("Сегодня ты уже получала предсказание ✨")
        return
    last_prediction_date[uid] = now
    await update.message.reply_text(random.choice(PREDICTIONS))

async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    card, meaning, reversed_meaning = random.choice(TAROT_CARDS)
    is_reversed = random.choice([True, False])
    meaning_text = reversed_meaning if is_reversed else meaning
    await update.message.reply_text(f"<b>{card}</b> ({'перевёрнутая' if is_reversed else 'прямая'}):\n{meaning_text}", parse_mode="HTML")

async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(random.choice(HUGS_MESSAGES))

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📜 <b>Правила клана:</b>\n"
        "1. Уважай других участниц.\n"
        "2. Не поддерживай войну.\n"
        "3. Ставь клановую приставку ঔ в ник.\n"
        "4. Соблюдай дисциплину.\n"
        "5. Нарушения караются удалением из клана.\n\n"
        "Полные правила тут: https://telegra.ph/Pravila-klana-৐OnlyGirls৐-05-29"
    )
    await update.message.reply_text(text, parse_mode="HTML")

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("pipisa", pipisa))
app.add_handler(CommandHandler("predskaz", predskaz))
app.add_handler(CommandHandler("tarot", tarot))
app.add_handler(CommandHandler("hugs", hugs))
app.add_handler(CommandHandler("rules", rules))

app.add_handler(ConversationHandler(
    entry_points=[CommandHandler("editprofile", editprofile)],
    states={PROFILE: [MessageHandler(filters.TEXT & ~filters.COMMAND, profile_input)]},
    fallbacks=[]
))

app.run_polling()
