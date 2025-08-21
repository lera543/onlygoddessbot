import logging
import random
from datetime import datetime
from telegram import Update, User
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863

logging.basicConfig(level=logging.INFO)

users = {}
pipisa_records = {}
last_predictions = {}
last_tarot = {}
lesbi_pair = None
last_lesbi = None
divorce_confirmations = {}

predictions = [
    "Ты на верном пути, не сдавайся! 💪",
    "Красота начинается с принятия себя 😍",
    "Действуй, даже если страшно 🚀",
]

tarot_cards = [
    ("🌞 Солнце", "Успех, радость, светлый путь", "Задержки, упадок энергии"),
    ("🌙 Луна", "Интуиция, тайны, сны", "Обман, путаница, страхи"),
    ("🧙‍♂️ Маг", "Возможности, энергия, контроль", "Манипуляции, обман, потеря контроля"),
]

def get_profile(uid):
    return users.get(uid, {
        "name": "",
        "nickname": "",
        "uid": "",
        "bday": "",
        "city": "",
        "social": "",
        "joined_date": "",
        "pipisa_height": 0.0,
        "quote": "",
        "married_to": None,
    })

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    text = (f"Добро пожаловать, {user.mention_html()}❣️\n"
            "Ознакомься пожалуйста с правилами клана https://telegra.ph/Pravila-klana-ঐOnlyGirlsঐ-05-29 🫶\n"
            "Важная информация всегда в закрепе❗️ Клановая приставка: ঔ")
    await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode='HTML')

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    data = get_profile(uid)
    married_info = f"💍 В браке с {data['married_to']}\n" if data["married_to"] else ""
    text = (
        f"🙋‍♀️ Имя: {data['name']}\n"
        f"🎮 Ник в игре: `{data['nickname']}`\n"
        f"🔢 UID: `{data['uid']}`\n"
        f"🎂 Дата рождения: {data['bday']}\n"
        f"🏙 Город: {data['city']}\n"
        f"📲 ТТ или inst: {data['social']}\n"
        f"📅 Дата вступления: {data['joined_date']}\n"
        f"🍆 Пиписа: {round(data['pipisa_height'], 1)} см\n"
        f"{married_info}📝 Девиз: {data['quote']}"
    )
    await update.message.reply_text(text, parse_mode='Markdown')

async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    uid = user.id
    args = context.args
    if len(args) < 8:
        await update.message.reply_text("Формат: /editprofile имя ник uid др город соцсеть дата цитата")
        return
    users[uid] = {
        "name": user.first_name,
        "nickname": args[1],
        "uid": args[2],
        "bday": args[3],
        "city": args[4],
        "social": args[5],
        "joined_date": args[6],
        "quote": " ".join(args[7:]),
        "pipisa_height": users.get(uid, {}).get("pipisa_height", 0.0),
        "married_to": users.get(uid, {}).get("married_to")
    }
    await update.message.reply_text("Профиль обновлён!")

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
    msg = (f"Пиписа выросла на +{change} см! 💦" if change > 0 else
           f"Ой... Пиписа уменьшилась на {abs(change)} см 🥲")
    users[uid] = data
    await update.message.reply_text(msg)

async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        target = context.args[0]
        await update.message.reply_text(f"🤗 {update.effective_user.mention_html()} обняла {target}!", parse_mode='HTML')
    else:
        text = random.choice([
            "🤗 Обнимашки для всех!",
            "🫂 Кто не обнимется — тот не играет в кастомке!",
            "🫂 Токсиков тоже иногда обнимают… по голове… табуреткой 🙃",
            "💖 Тепло и поддержка для всех девочек чата!",
            "🌈 Пусть твой день будет мягким как пледик 🧸"
        ])
        await update.message.reply_text(text)

async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    today = datetime.now().date()
    if last_predictions.get(uid) == today:
        await update.message.reply_text("🔮 Уже получала предсказание сегодня!")
    else:
        last_predictions[uid] = today
        await update.message.reply_text(f"🔮 {random.choice(predictions)}")

async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    today = datetime.now().date()
    if last_tarot.get(uid) == today:
        await update.message.reply_text("🃏 Расклад доступен раз в день!")
        return
    card, normal, reverse = random.choice(tarot_cards)
    meaning = random.choice([normal, reverse])
    last_tarot[uid] = today
    await update.message.reply_text(f"**{card}** — {meaning}", parse_mode='Markdown')

async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last_lesbi, lesbi_pair
    today = datetime.now().date()
    if last_lesbi == today:
        await update.message.reply_text("👭 Пара уже выбрана сегодня!")
        return
    members = list(users.values())
    if len(members) < 2:
        await update.message.reply_text("Недостаточно участниц для пары")
        return
    pair = random.sample(members, 2)
    lesbi_pair = (pair[0]["name"], pair[1]["name"])
    last_lesbi = today
    text = f"💘 Сегодняшняя парочка: {lesbi_pair[0]} и {lesbi_pair[1]} — обнимайтесь крепко!"
    await context.bot.send_message(chat_id=CHAT_ID, text=text)

async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи, кого хочешь предложить: /love @username")
        return
    uid = update.effective_user.id
    partner_username = context.args[0].replace("@", "")
    for pid, pdata in users.items():
        if pdata["nickname"] == partner_username:
            users[uid]["married_to"] = pdata["name"]
            pdata["married_to"] = users[uid]["name"]
            await context.bot.send_message(chat_id=CHAT_ID, text=f"💍 Свадьба! {pdata['name']} теперь в браке с {users[uid]['name']} 💞")
            return
    await update.message.reply_text("Пользователь не найден!")

async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    partner = users.get(uid, {}).get("married_to")
    if not partner:
        await update.message.reply_text("Ты не в браке!")
        return
    divorce_confirmations[uid] = partner
    await update.message.reply_text("Подтверди развод: /confirmdivorce")

async def confirmdivorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    partner_name = divorce_confirmations.pop(uid, None)
    if not partner_name:
        await update.message.reply_text("Нет подтверждённого развода")
        return
    users[uid]["married_to"] = None
    for pid, pdata in users.items():
        if pdata["name"] == partner_name:
            pdata["married_to"] = None
            await context.bot.send_message(chat_id=CHAT_ID, text=f"💔 Развод! {users[uid]['name']} и {partner_name} расстались.")
            return

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Возможности бота:\n"
        "/profile — посмотреть профиль\n"
        "/editprofile — изменить профиль\n"
        "/grow — растить пипису\n"
        "/top5 — топ пипис\n"
        "/predskaz — предсказание\n"
        "/tarot — карта Таро\n"
        "/lesbi — случайная парочка\n"
        "/hugs — обнимашки\n"
        "/love @юзер — свадьба\n"
        "/divorce — развод\n"
        "/confirmdivorce — подтвердить развод\n"
        "/about — это меню"
    )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("profile", profile))
app.add_handler(CommandHandler("editprofile", editprofile))
app.add_handler(CommandHandler("grow", grow))
app.add_handler(CommandHandler("predskaz", predskaz))
app.add_handler(CommandHandler("tarot", tarot))
app.add_handler(CommandHandler("lesbi", lesbi))
app.add_handler(CommandHandler("hugs", hugs))
app.add_handler(CommandHandler("love", love))
app.add_handler(CommandHandler("divorce", divorce))
app.add_handler(CommandHandler("confirmdivorce", confirmdivorce))
app.add_handler(CommandHandler("about", about))
app.run_polling()
