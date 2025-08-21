import logging
import random
import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler, ConversationHandler

TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

users = {}
married = set()
lesbi_couples = {}
last_prediction_date = {}
last_lesbi_date = None

with open("predictions.txt", "r", encoding="utf-8") as f:
    PREDICTIONS = f.read().split("\n")

TAROT_CARDS = [
    ("Шут 🤡", "новое начало, спонтанность, наивность", "безрассудство, неопределённость"),
    ("Маг 🧙", "воля, мастерство, творческая энергия", "манипуляции, обман, неуверенность"),
    ("Жрица 🔮", "интуиция, тайна, внутренняя мудрость", "скрытность, отстранённость"),
    ("Императрица 👑", "изобилие, забота, плодородие", "зависимость, расточительность"),
    ("Император 🧱", "власть, стабильность, защита", "деспотизм, жесткость"),
    ("Жрец 🙏", "духовность, традиции, знание", "догматизм, ограниченность"),
    ("Влюблённые 💞", "любовь, выбор, единство", "раздор, нерешительность"),
    ("Колесница 🛞", "победа, движение, контроль", "потеря контроля, агрессия"),
    ("Сила 🦁", "смелость, терпение, уверенность", "сомнение, страх"),
    ("Отшельник 🕯️", "поиск истины, уединение", "изоляция, замкнутость"),
    ("Колесо Фортуны 🎡", "судьба, перемены, удача", "непредсказуемость, застой"),
    ("Справедливость ⚖️", "равновесие, честность", "нечестность, предвзятость"),
    ("Повешенный 🙃", "жертва, пауза, переосмысление", "застой, беспомощность"),
    ("Смерть 💀", "конец, трансформация, обновление", "сопротивление переменам"),
    ("Умеренность 🧘", "гармония, баланс, терпение", "дисбаланс, чрезмерность"),
    ("Дьявол 😈", "искушение, зависимость, страсть", "освобождение, контроль"),
    ("Башня 🗼", "внезапные перемены, крах", "избежание разрушения"),
    ("Звезда 🌟", "надежда, вдохновение, исцеление", "пессимизм, потеря веры"),
    ("Луна 🌙", "иллюзии, страхи, интуиция", "заблуждение, тревожность"),
    ("Солнце ☀️", "радость, успех, просветление", "самодовольство, упрямство"),
    ("Суд ⚰️", "пробуждение, искупление, судьба", "сожаление, страх перемен"),
    ("Мир 🌍", "завершение, целостность, успех", "незавершённость, задержки")
]

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

# Дальше идут все функции: start, profile, editprofile, grow, top5, rating и т.д.
# ... (добавляются все функции согласно последней версии)

# Регистрируем команды
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("editprofile", editprofile))
app.add_handler(CommandHandler("grow", grow))
app.add_handler(CommandHandler("top5", top5))
app.add_handler(CommandHandler("rating", fullrating))
app.add_handler(CommandHandler("predskaz", predskaz))
app.add_handler(CommandHandler("tarot", tarot))
app.add_handler(CommandHandler("rules", rules))
app.add_handler(CommandHandler("about", about))
app.add_handler(CommandHandler("lesbi", lesbi))
app.add_handler(CommandHandler("hugs", hugs))
app.add_handler(CommandHandler("love", love))
app.add_handler(CommandHandler("divorce", divorce))
app.add_handler(CommandHandler("confirmdivorce", confirmdivorce))

app.run_polling()
