import logging
import random
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, User
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863

logging.basicConfig(level=logging.INFO)

users = {}
pipisa_records = {}
weddings = {}
divorce_confirmations = {}
last_predictions = {}
last_tarot = {}
lesbi_pair = None
last_lesbi = None

predictions = [
    # 200 предсказаний: 100 жизненных, 50 красоты, 50 мотивации (смайлики добавлены)
    "Ты на верном пути, не сдавайся! 💪",
    "Красота начинается с принятия себя 😍",
    "Действуй, даже если страшно 🚀",
    # ... (и остальные предсказания)
]

tarot_cards = [
    ("🌞 Солнце", "Успех, радость, светлый путь", "Задержки, упадок энергии"),
    ("🌙 Луна", "Интуиция, тайны, сны", "Обман, путаница, страхи"),
    ("🧙‍♂️ Маг", "Возможности, энергия, контроль", "Манипуляции, обман, потеря контроля"),
    # ... остальные старшие арканы
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (f"Добро пожаловать, {user.mention_html()}❣️\n"
            "Ознакомься пожалуйста с правилами клана "
            "(https://telegra.ph/Pravila-klana-ঐOnlyGirlsঐ-05-29)🫶\n"
            "Важная информация всегда в закрепе❗️ Клановая приставка: ঔ")
    await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')

def get_profile(uid):
    return users.get(uid, {
        "name": "",
        "nickname": "",
        "bday": "",
        "city": "",
        "social": "",
        "joined_date": "",
        "pipisa_height": 0.0,
        "quote": "",
        "married_to": None
    })

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    data = get_profile(uid)
    married_info = f"💍 В браке с {data['married_to']}\n" if data["married_to"] else ""
    text = (f"🙋‍♀️ Имя: {data['name']}\n🎮 Ник в игре: {data['nickname']}\n🎂 Дата рождения: {data['bday']}\n🏙 Город: {data['city']}\n📲 Соц.сеть: {data['social']}\n📅 Дата вступления: {data['joined_date']}\n🍆 Рост пиписы: {round(data['pipisa_height'], 1)} см\n{married_info}📝 Цитата: {data['quote']}")
    await update.message.reply_text(text)

async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    data = get_profile(uid)
    args = context.args
    if len(args) < 7:
        await update.message.reply_text("Используй формат: /editprofile Имя Ник_в_игре ДР Город Соцсеть ДатаВступления Цитата")
        return
    data["name"] = user.mention_html()
    data["nickname"] = args[0]
    data["bday"] = args[1]
    data["city"] = args[2]
    data["social"] = args[3]
    data["joined_date"] = args[4]
    data["quote"] = " ".join(args[5:])
    users[uid] = data
    await update.message.reply_text("Профиль обновлен!", parse_mode='HTML')

async def grow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    now = datetime.now()
    data = get_profile(uid)
    key = f"pipisa_time_{uid}"
    if context.chat_data.get(key) and context.chat_data[key].date() == now.date():
        await update.message.reply_text("Пипису можно растить только раз в день!")
        return

    change = round(random.uniform(-10, 10), 1)
    if -0.1 < change < 0.1:
        change = 0.1 if random.random() > 0.5 else -0.1

    data["pipisa_height"] += change
    context.chat_data[key] = now

    if change > 0:
        msg = random.choice([
            f"Пиписа выросла на +{change} см! 💦",
            f"Вау! +{change} см к удовольствию 😏",
            f"Теперь твоя пиписа {round(data['pipisa_height'],1)} см! 🍆"
        ])
    else:
        msg = random.choice([
            f"Ой... Пиписа уменьшилась на {abs(change)} см 🥲",
            f"Минус {abs(change)} см... надо постараться лучше! 😿",
            f"Твоя пиписа теперь {round(data['pipisa_height'],1)} см. Не расстраивайся 💔"
        ])
    users[uid] = data
    await update.message.reply_text(msg)

async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = sorted(users.items(), key=lambda x: x[1].get("pipisa_height", 0), reverse=True)[:5]
    text = "🏆 ТОП 5 пипис:\n" + "\n".join(
        [f"{i+1}. {v['name']} — {round(v['pipisa_height'],1)} см" for i, (k,v) in enumerate(top)]
    )
    await update.message.reply_text(text, parse_mode='HTML')

async def fullrating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    top = sorted(users.items(), key=lambda x: x[1].get("pipisa_height", 0), reverse=True)
    text = "📊 Рейтинг пипис:\n" + "\n".join(
        [f"{i+1}. {v['name']} — {round(v['pipisa_height'],1)} см" for i, (k,v) in enumerate(top)]
    )
    await update.message.reply_text(text, parse_mode='HTML')

async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    now = datetime.now().date()
    if last_predictions.get(uid) == now:
        await update.message.reply_text("🔮 Предсказание уже было сегодня!")
        return
    last_predictions[uid] = now
    await update.message.reply_text(f"🔮 {random.choice(predictions)}")

async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    now = datetime.now().date()
    if last_tarot.get(uid) == now:
        await update.message.reply_text("🃏 Расклад Таро доступен раз в день!")
        return
    card, normal, reverse = random.choice(tarot_cards)
    is_reversed = random.choice([True, False])
    text = f"**{card}** — {reverse if is_reversed else normal}"
    await update.message.reply_text(text, parse_mode='Markdown')
    last_tarot[uid] = now

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("rules.txt", encoding="utf-8") as f:
        await update.message.reply_text(f.read())

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Возможности бота: \n"
        "/profile — посмотреть профиль\n"
        "/editprofile — изменить профиль\n"
        "/grow — растить пипису\n"
        "/top5 — топ пипис\n"
        "/rating — весь рейтинг\n"
        "/predskaz — предсказание\n"
        "/tarot — карта Таро\n"
        "/lesbi — случайная парочка\n"
        "/hugs — обнимашки\n"
        "/love @юзер — свадьба\n"
        "/divorce @юзер — развод\n"
        "/rules — правила клана\n"
        "/about — это меню"
    )

# Лесби пары
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_lesbi, lesbi_pair
    now = datetime.now().date()
    if last_lesbi == now:
        await update.message.reply_text("👭 Пара уже выбрана сегодня!")
        return
    members = list(users.items())
    if len(members) < 2:
        await update.message.reply_text("Недостаточно участниц для выбора пары")
        return
    pair = random.sample(members, 2)
    lesbi_pair = (pair[0][1]["name"], pair[1][1]["name"])
    last_lesbi = now
    text = random.choice([
        f"💘 Сегодняшняя парочка: {lesbi_pair[0]} и {lesbi_pair[1]} — обнимайтесь крепко!",
        f"🌈 Любовь витает в воздухе: {lesbi_pair[0]} 💞 {lesbi_pair[1]}"
    ])
    await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')

# Обнимашки
async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        user = context.args[0]
        await update.message.reply_text(f"🤗 {update.effective_user.mention_html()} обняла {user}!", parse_mode='HTML')
    else:
        await update.message.reply_text("🤗 Обнимашки для всех в чате! 🫂")

# Свадьба
async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи, кого хочешь предложить /love @username")
        return
    target = context.args[0].replace("@", "")
    uid = update.effective_user.id
    users[uid]["proposal"] = target
    await update.message.reply_text(f"💍 {update.effective_user.mention_html()} сделала предложение @{target}. Ждём ответа!", parse_mode='HTML')

async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if not users[uid].get("married_to"):
        await update.message.reply_text("Ты не в браке!")
        return
    partner = users[uid]["married_to"]
    divorce_confirmations[uid] = partner
    await update.message.reply_text(f"Ты точно хочешь развестись с {partner}? Напиши /confirmdivorce")

async def confirmdivorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    partner_name = divorce_confirmations.pop(uid, None)
    if not partner_name:
        await update.message.reply_text("Нет запроса на развод")
        return
    for k, v in users.items():
        if v["name"] == partner_name:
            v["married_to"] = None
            users[uid]["married_to"] = None
            await context.bot.send_message(chat_id=CHAT_ID,
                text=f"💔 Развод! {users[uid]['name']} и {partner_name} расстались.")
            return

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
