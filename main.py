# -*- coding: utf-8 -*-
import json
import logging
import random
from typing import Optional
from datetime import datetime, date, time
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ChatMemberHandler,
    ConversationHandler, ContextTypes, filters
)

# ===================== НАСТРОЙКИ =====================
TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863  # общий чат
DATA_FILE = Path("data.json")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("OnlyGirlsBot")

# ===================== ХРАНИЛИЩЕ =====================
# state:
# users: {
#   user_id(str): {
#     "name" (HTML-кликабельно на профиль по введённому имени),
#     "first_name", "username",
#     "nickname", "uid", "bday", "city",
#     "tiktok", "quote",
#     "pipisa", "last_pipisa", "last_prediction"
#   }
# }
# known_users: [int, ...]
# last_lesbi_date: "YYYY-MM-DD"
# last_lesbi_pair: [user_id_a(int), user_id_b(int)]
state = {
    "users": {},
    "known_users": [],
    "last_lesbi_date": None,
    "last_lesbi_pair": None
}

def load_state():
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            state.update(data)
        except Exception as e:
            logger.warning(f"Не удалось загрузить data.json: {e}")

def save_state():
    try:
        DATA_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception as e:
        logger.error(f"Ошибка сохранения data.json: {e}")

load_state()

# ===================== ВСПОМОГАТЕЛЬНЫЕ =====================
def today_str() -> str:
    return date.today().isoformat()

def ensure_user(user_id: int, first_name: Optional[str] = None, username: Optional[str] = None):
    suid = str(user_id)
    if suid not in state["users"]:
        state["users"][suid] = {
            "name": "",
            "first_name": first_name or "",
            "username": username or "",
            "nickname": "",
            "uid": "",
            "bday": "",
            "city": "",
            "tiktok": "",
            "quote": "",
            "pipisa": 0.0,
            "last_pipisa": None,
            "last_prediction": None,
        }
    else:
        if first_name:
            state["users"][suid]["first_name"] = first_name
        if username:
            state["users"][suid]["username"] = username

    if user_id not in state.get("known_users", []):
        state["known_users"].append(user_id)

def tg_link_from_id(user_id: int, text: str) -> str:
    return f'<a href="tg://user?id={user_id}">{text}</a>'

def display_user(user_id: int) -> str:
    """Красивое имя участницы: введённое имя (кликабельно), или first_name/username, или ссылка по id."""
    suid = str(user_id)
    u = state["users"].get(suid)
    if u:
        if u.get("name"):
            return u["name"]
        if u.get("first_name"):
            return tg_link_from_id(user_id, u["first_name"])
        if u.get("username"):
            return "@" + u["username"]
    return tg_link_from_id(user_id, "девочка")

def is_url(s: str) -> bool:
    return isinstance(s, str) and (s.startswith("http://") or s.startswith("https://"))

# ===================== ПРИВЕТСТВИЕ НОВЫХ =====================
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    old = cmu.old_chat_member.status
    new = cmu.new_chat_member.status

    if (old in ("left", "kicked")) and (new in ("member", "administrator", "creator")):
        user = cmu.new_chat_member.user
        ensure_user(user.id, user.first_name, user.username)
        save_state()

        text = (
            f"Добро пожаловать, {user.mention_html()}❣️ "
            f'Ознакомься пожалуйста с правилами клана '
            f'(<a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a>)🫶 '
            f"Важная информация всегда в закрепе❗️ Клановая приставка: ঔ"
        )
        await context.bot.send_message(chat_id=cmu.chat.id, text=text, parse_mode="HTML")

# Обновляем known_users по любому сообщению
async def track_speaker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_user:
        return
    u = update.effective_user
    ensure_user(u.id, u.first_name, u.username)
    save_state()

# ===================== /START и /ABOUT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.first_name, user.username)
    save_state()
    await update.message.reply_text(
        "Привет! Я — Мать Богинь для клана OnlyGirls 💖\n"
        "Напиши /about чтобы узнать мои команды."
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "✨ Команды:\n"
        "/editprofile — заполнить/обновить профиль (пошагово)\n"
        "/profile — показать твой профиль\n"
        "/pipisa — вырастить/уменьшить пипису (1 раз в день)\n"
        "/top5 — топ-5 по пиписе\n"
        "/rating — полный рейтинг пипис\n"
        "/predskaz — предсказание дня (1 раз в день)\n"
        "/hugs [@юзер] — обнимашки (для всех или указанного)\n"
        "/compliment [@юзер] — комплимент (кому-то или рандом)\n"
        "/lesbi — лесби-пара дня (1 раз в день)\n"
        "/role @юзер — «кто сегодня самая…»\n"
        "/rules — правила клана (ссылка)"
    )

# ===================== /RULES (ссылка) =====================
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Котик, правила клана <a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a> 🫶',
        parse_mode="HTML"
    )

# ===================== ПРОФИЛЬ (пошагово) =====================
(
    STEP_NAME,
    STEP_NICK,
    STEP_UID,
    STEP_BDAY,
    STEP_CITY,
    STEP_TIKTOK,
    STEP_QUOTE
) = range(7)

def render_profile(u: dict) -> str:
    name = u.get("name") or "не указано"
    nickname = u.get("nickname") or ""
    uid = u.get("uid") or ""
    bday = u.get("bday") or "не указано"
    city = u.get("city") or "не указан"
    tiktok = u.get("tiktok") or ""
    quote = u.get("quote") or "—"
    pipisa = float(u.get("pipisa") or 0.0)

    # TikTok строка
    if tiktok:
        if is_url(tiktok):
            tt_line = f'📲 TikTok: <a href="{tiktok}">TikTok</a>'
        else:
            at = tiktok if tiktok.startswith("@") else f"@{tiktok}"
            tt_line = f"📲 TikTok: {at}"
    else:
        tt_line = "📲 TikTok: не указан"

    text = (
        f"🙋‍♀️ Имя: {name}\n"
        f"🎮 Ник в игре: <code>{nickname}</code>\n"
        f"🔢 UID: <code>{uid}</code>\n"
        f"🎂 Дата рождения: {bday}\n"
        f"🏙 Город: {city}\n"
        f"{tt_line}\n"
        f"🍆 Пиписа: {pipisa:.1f} см\n"
        f"📝 Девиз: {quote}"
    )
    return text

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.username)
    u = state["users"].get(uid)
    await update.message.reply_text(render_profile(u), parse_mode="HTML")

async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    u = update.effective_user
    ensure_user(u.id, u.first_name, u.username)
    context.user_data["profile_answers"] = {}
    await update.message.reply_text("Как тебя зовут? (имя)")
    return STEP_NAME

async def step_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    typed = (update.message.text or "").strip()
    uid = update.effective_user.id
    clickable_name = tg_link_from_id(uid, typed if typed else (update.effective_user.first_name or "девочка"))
    context.user_data["profile_answers"]["name"] = clickable_name
    await update.message.reply_text("Какой у тебя ник в игре?")
    return STEP_NICK

async def step_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["nickname"] = (update.message.text or "").strip()
    await update.message.reply_text("Какой у тебя UID?")
    return STEP_UID

async def step_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["uid"] = (update.message.text or "").strip()
    await update.message.reply_text("Когда у тебя день рождения? (например, 01.01.2000 или 01.01)")
    return STEP_BDAY

async def step_bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["bday"] = (update.message.text or "").strip()
    await update.message.reply_text("Из какого ты города?")
    return STEP_CITY

async def step_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["city"] = (update.message.text or "").strip()
    await update.message.reply_text("Оставь TikTok: ссылку или просто ник (@username):")
    return STEP_TIKTOK

async def step_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["tiktok"] = (update.message.text or "").strip()
    await update.message.reply_text("Поделись своим девизом или любимой цитатой:")
    return STEP_QUOTE

async def step_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["quote"] = (update.message.text or "").strip()
    suid = str(update.effective_user.id)
    ensure_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.username)

    stored = state["users"][suid]
    for k, v in context.user_data["profile_answers"].items():
        stored[k] = v

    save_state()
    await update.message.reply_text("Профиль обновлён ✅")
    return ConversationHandler.END

# ===================== /pipisa (1 раз в день) =====================
PIPISA_UP_REACTIONS = [
    "Она стремится к вершинам! 📈",
    "Вперед и выше — гордимся! 🥳",
    "Так растёт только легенда! 🌟",
    "Сияет и радует хозяйку! ✨",
]
PIPISA_DOWN_REACTIONS = [
    "Ничего, завтра вернём позиции 💪",
    "Иногда и героям нужен отдых 🌧️",
    "Обнимем — и всё пройдёт 🫂",
    "Сменим вайб — пойдёт вверх 🌈",
]

def _rand_delta():
    d = round(random.uniform(-10.0, 10.0), 1)
    if d == 0.0:
        d = 0.1 if random.random() > 0.5 else -0.1
    return d

async def pipisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suid = str(update.effective_user.id)
    ensure_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.username)
    u = state["users"][suid]

    if u.get("last_pipisa") == today_str():
        await update.message.reply_text("Пипису можно растить/мерить только раз в день! 🌱")
        return

    delta = _rand_delta()
    new_val = round(float(u.get("pipisa", 0.0)) + delta, 1)
    if new_val < 0:
        new_val = 0.0

    u["pipisa"] = new_val
    u["last_pipisa"] = today_str()
    save_state()

    if delta > 0:
        phrase = random.choice([
            f"🍆 Твоя пиписа выросла на {delta:.1f} см! {random.choice(PIPISA_UP_REACTIONS)} Теперь: {new_val:.1f} см.",
            f"🍆 Ого! +{delta:.1f} см — вот это рост! {random.choice(PIPISA_UP_REACTIONS)} Текущий размер: {new_val:.1f} см.",
        ])
    else:
        phrase = random.choice([
            f"🍆 Оу… пиписа уменьшилась на {abs(delta):.1f} см. {random.choice(PIPISA_DOWN_REACTIONS)} Сейчас: {new_val:.1f} см.",
            f"🍆 Немного просела ({abs(delta):.1f} см). {random.choice(PIPISA_DOWN_REACTIONS)} Текущий размер: {new_val:.1f} см.",
        ])
    await update.message.reply_text(phrase)

# ===================== РЕЙТИНГИ =====================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)[:5]
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще 🌱")
        return
    text = "🏆 ТОП-5 пипис клана:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or display_user(int(uid))}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще 🌱")
        return
    text = "📊 Полный рейтинг пипис:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or display_user(int(uid))}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ===================== ПРЕДСКАЗАНИЯ (200 штук) =====================
PREDICTIONS = [
    # 1–100 универсальные
    "Сегодня твой день — даже если облачно ☁️",
    "Улыбка решит больше, чем кажется 😊",
    "Делай по любви — и будет кайф 💖",
    "Вселенная сегодня на твоей стороне ✨",
    "Ты видишь больше, чем другие — доверься себе 👁️",
    "Маленький шаг тоже движение вперёд 👣",
    "Слухи остаются слухами — будь выше 🕊️",
    "Пусть душа сегодня потанцует 💃",
    "Ты — чьё-то «повезло» 🍀",
    "Скажи себе «молодец» — ты это услышишь 🥰",
    "Там, где твоё внимание, там и твоя сила 🌱",
    "Лучшее настроение приходит после тёплого чая 🍵",
    "Чудеса любят смелых — рискни чуть-чуть 🌈",
    "Ты украшение этого дня 💫",
    "Каждый добрый жест возвращается бумерангом 🎯",
    "Тепло от твоей улыбки уже спасает мир 🌷",
    "Вдох-выдох. Всё по силам 🤍",
    "Ты уже справлялась — справишься и сейчас 🦋",
    "Верь себе громче, чем сомнениям 🔊",
    "Пусть будет немного проще, чем вчера 💌",
    "Даже маленькая забота о себе — это победа 🌸",
    "Ласково с собой — мир ответит тем же 🫶",
    "Сегодня тебе повезёт там, где ты искренна 🌟",
    "Найди 10 минут тишины — это суперсила 🔕",
    "Позволь себе отдых без оправданий 🧸",
    "Кто-то очень гордится тобой — правда 💞",
    "Ты там, где нужно — и всё окей 📍",
    "Проще отнесись — и станет легче ☁️",
    "Сделай добро втихаря — кайф вернётся 🍫",
    "Смех — лучший спутник дня 😂",
    "Термос с теплом есть: это ты ☕️",
    "Никакой спешки — только ритм сердца ❤️",
    "Твои границы — это нежность к себе 🛡️",
    "Сегодня идеальный день не быть идеальной 🧩",
    "Сделай шаг и посмотри, как мир подвинется 🚪",
    "Пусть музыка дня будет доброй 🎧",
    "Ты — главный подарок жизни 🎁",
    "Сомнение не рулит — рулит опыт 🚗",
    "Где забота — там и силы 🌿",
    "Сегодня «можно» громче, чем «надо» 🔔",
    "Уверенность — это маленькие «получилось» 📈",
    "Не обесценивай то, что уже сделала 🏆",
    "Поблагодари себя за прошлую тебя 🙏",
    "Пусть рядом будут тёплые люди 🧑‍🤝‍🧑",
    "Стань себе самой нежной подругой 💐",
    "Дыши медленнее — мысли станут мягче 🍃",
    "Двигайся в темпе души, не марафона 🏃‍♀️",
    "Ставь точку там, где устала — можно ⛔️",
    "Заслуженный отдых — тоже действие 🛌",
    "Сегодня тебя ждёт маленькая радость 🎈",
    "Ты — не задачи, ты — человек 💗",
    "Ласка к себе — не роскошь, а база 🧴",
    "Будь внимательна к знакам — вселенная шепчет ✉️",
    "Выбери одно дело и сделай его красиво 🎀",
    "Ничего страшного в «не хочу» 🚫",
    "Смени фон на более добрый 🌅",
    "Твоё спокойствие важнее чужой спешки 🧘‍♀️",
    "Ты всё контролируешь — в рамках возможного 🎛️",
    "Не сравнивай — ты другая, и это плюс 🌙",
    "Пусть день будет мягким и тёплым 🧣",
    "Радость в мелочах — найди три 📝",
    "Ты сильнее, чем тебе кажется 🗝️",
    "Один шаг за раз — и гора меньше 🏔️",
    "Скажи «да» себе и «нет» лишнему 🚧",
    "Выбери себя без чувства вины 💞",
    "Тебе можно просто быть 🌼",
    "Грусть — это тоже чувство, не враг 🌧️",
    "Забота о теле — это любовь, а не задача 🛁",
    "С тебя начинается уют вокруг 🕯️",
    "То, что твоё — тебя найдёт 📬",
    "Ошибка — не ты, а событие 🧯",
    "Важно: ты делаешь достаточно ✔️",
    "Сегодня улыбка найдёт тебя сама 😊",
    "У тебя хороший вкус на людей 💌",
    "Спрячь телефон — поймай реальность 🌤️",
    "План «Б» — это не поражение, а мудрость 🧠",
    "Ты даёшь другим чувство дома 🏡",
    "Твоё «не хочу» тоже достойно уважения 🚷",
    "С каждым днём ты всё честнее с собой 💭",
    "Мозг — не враг, просто уставший друг 🧠",
    "Выбор — это власть. Сегодня она у тебя 👑",
    "Тебя ждёт совпадение, в которое сложно не поверить ✨",
    "Твои слова сегодня кому-то очень помогут 🗣️",
    "Твоя нежность — мощнее шума мира 🎧",
    "Отпусти то, что не твоё — станет легче 🎈",
    "Сегодня настроение чинить носочки жизни 🧶",
    "Ты заметно выросла — даже если не видишь 📏",
    "Поблагодари утро — и оно ответит 🌞",
    "Ты приносишь порядок хаосу 🌪️→🌈",
    "Твоя интуиция сегодня — лучший навигатор 🧭",
    "Смелость — это шёпот «попробуй» 🔔",
    "Вечером тебя ждет уютная награда 🍪",
    "Обними себя. Сильно. Прямо сейчас 🫂",
    "Твоя доброта — редкая валюта 💎",
    "Ты не обязана быть сильной 24/7 🪴",
    "Сегодня можно просто жить без подвигов 🌿",
    "Внутри тебя больше света, чем кажется 🕯️",
    "Ты — чудо, которое с собой каждый день ✨",
    "Самое лучшее впереди — и это близко 🔮",

    # 101–150 про красоту / самооценку
    "Сегодня ты особенно красивая — факт 😍",
    "Твои глаза сияют ярче, чем обычно ✨",
    "Твоя улыбка — лучший хайлайтер 😊",
    "Кожа говорит «спасибо» за заботу 💧",
    "Ты — ходячая эстетика дня 🎨",
    "Волосы сегодня как в рекламе 💁‍♀️",
    "Твой стиль — вдохновение для других 👗",
    "Красота в деталях — у тебя всё блестит 💅",
    "Ты — галерея нежности и вкуса 🖼️",
    "Любое зеркало сегодня твоё фан-клуб 💖",
    "Селфи сегодня обязано случиться 📸",
    "Тебе идёт спокойствие — шик стайл 🧘‍♀️",
    "Ты выглядишь так, будто выспалась идеально 😴✨",
    "Твоё «без фильтра» — лучше любого фильтра 🌟",
    "Светишься изнутри — это заметно 🔆",
    "Твой образ — вау даже в пижаме 🛌💃",
    "Маник — топ! Даже если его нет 💅😄",
    "Ресницы говорят: «мы великолепны» 👁️",
    "Брови сегодня дружат с космосом 🌌",
    "Ты — девочка обложки, но уютной 🧸",
    "Сегодня ты точно попадёшь в чьи-то мысли 💭",
    "Твои черты — мягкая поэзия лица 📝",
    "Ты — гармония без усилий 🎼",
    "У тебя идеальная посадка улыбки 😁",
    "Красота, которая делает мир добрее 💗",
    "Твоё присутствие — эстетический апгрейд 💫",
    "Сегодня ты — муза для кого-то 🎻",
    "Тебя хочется рисовать акварелью 🎨💧",
    "В каждом движении — грация 🦢",
    "Ты — тот самый вайб «ух!» 💥",
    "Косметичка отдыхает — ты и так сияешь ✨",
    "Красота без шума — твой стиль 🤍",
    "Ты — доказательство, что нежность — сила 💪🌸",
    "Смотришься дороже, чем все тренды 💎",
    "Твой взгляд — отдельный вид искусства 🖤",
    "Ты — сладкий баланс и ухоженность 🍯",
    "Тебе идёт всё, что ты любишь 💘",
    "Сегодня ты — тёплая эстетика осени 🍂",
    "Эта прядь волос — шедевр 🎨",
    "Ты — мягкий фокус мира 📷",
    "Сияй! Мир не ослепнет, он привыкнет ☀️",
    "Ты — главная модель своего дня 👠",
    "Любая поза — как обложка 💃",
    "Ты — красота, которая лечит 🌺",
    "Сегодня ногти — загляденье 💅✨",
    "Твоё «как обычно» — уже прекрасно 🌷",
    "Ты — эксперт по милоте 🧁",
    "Ты — фильтр «романтика» в реальности 💟",
    "Эстетика в теле человека — это ты 🫶",

    # 151–200 мотивация
    "Можешь меньше — делай меньше. Но делай 🧩",
    "Начни с 5 минут — и поедет 🚴‍♀️",
    "Твоя дисциплина — это забота, а не кнут 🎗️",
    "Делай тихо — результат скажет громко 📢",
    "Перфекционизм выключен — прогресс включён 🔛",
    "Планируй по-реальному, а не «как надо» 🗓️",
    "Лучше стабильно, чем идеально ✅",
    "Разреши себе ошибаться — это путь 🛤️",
    "Сделай фокус на одном — будет прорыв 🎯",
    "Попроси помощь — это зрелость 🤝",
    "Раздели задачу на атомы — и вперёд ⚛️",
    "Сделай первым делом самое простое 🧸",
    "Пиши маленькие галочки — мозг обожает ✔️",
    "Отдых — часть плана, не бонус 😴",
    "Сравни себя с собой вчера — успех 📈",
    "Ставь дедлайны с любовью ⏳💗",
    "Не усложняй — выбирай понятное 🛠️",
    "Сделай на 60% — это уже отлично 🥳",
    "Доверяй процессу — результат придёт 🚪",
    "Учись у сбоев — там подсказки 📚",
    "Окружай себя поддержкой — это топ 🧑‍🤝‍🧑",
    "Твоя скорость — нормальная скорость 🐢",
    "Выпей воды и продолжай 💧",
    "Награди себя за маленький шаг 🍫",
    "Попробуй ещё раз — уже легче 🔁",
    "Не всё срочно — отделяй важное 🧭",
    "Где ясно, там легче — упрощай 🧹",
    "Сделай первый черновик — он спасает 📝",
    "Подумай письменно — прояснится 🖊️",
    "Твоя система работает — верь ей ⚙️",
    "У тебя есть право не успевать 💬",
    "Сохраняй энергию — говори «нет» 🔋",
    "Смотри на горизонт, а не на шум 🌅",
    "Выбери одно «да» на день ✅",
    "Делай чуть-чуть ежедневно — великое случится 📆",
    "Отмечай победы — мозгу нужна обратная связь 🧠",
    "Если страшно — раздели на шаги 🪜",
    "Доводи до «достаточно», а не «идеально» 🧩",
    "Параллельно — хуже, последовательно — лучше 🧵",
    "Ты умеешь — просто начни прямо сейчас 🚀",
]

async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    suid = str(update.effective_user.id)
    ensure_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.username)
    u = state["users"][suid]
    if u.get("last_prediction") == today_str():
        await update.message.reply_text("🔮 Предсказание уже было сегодня!")
        return
    u["last_prediction"] = today_str()
    save_state()
    await update.message.reply_text(f"🔮 {random.choice(PREDICTIONS)}")

# ===================== HUGS =====================
HUGS_POOL = [
    "🤗 {a} крепко обняла {b} — тепло доставлено по адресу 🧸",
    "💞 {a} нежно прижалась к {b} — пусть тревоги тают 🌷",
    "🥰 {a} согрела {b} своими обнимашками — зарядилась любовью!",
    "🫶 {a} и {b} — сегодня самый милый дуэт!",
    "Кто не обнимется — тот не играет в кастомке!",
    "🫂 Токсиков тоже иногда обнимают… по голове… табуреткой 🙃",
    "Передаю мягкость, заботу и печеньку 🍪 — {a} → {b}",
    "Крепко-крепко и очень нежно — трепещи, грусть! 🫂  {a} обняла {b}",
    "Пусть тревоги уменьшаются на 50% после этих объятий 🌸  {a} для {b}",
]

async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id, update.effective_user.first_name, update.effective_user.username)
    me = update.effective_user
    if context.args:
        target = context.args[0]
        msg = random.choice([
            f"🤗 {me.mention_html()} обняла {target}! Тепло доставлено 🧸",
            f"💞 {me.mention_html()} отправила объятия {target}. Всё будет хорошо 🌷",
        ])
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    pool = [uid for uid in state.get("known_users", []) if uid != me.id]
    if not pool:
        await update.message.reply_text("Обнимашки для всех в чате! 🫂")
        return
    target_id = random.choice(pool)
    a = me.mention_html()
    b = display_user(target_id)
    tpl = random.choice(HUGS_POOL)
    if "{a}" in tpl or "{b}" in tpl:
        text = tpl.format(a=a, b=b)
    else:
        text = f"{a} обняла {b} — {tpl}"
    await update.message.reply_text(text, parse_mode="HTML")

# ===================== КОМПЛИМЕНТЫ =====================
COMPLIMENTS = [
    "Ты сегодня светишься сильнее звезды ✨",
    "Твоя улыбка — мой личный антистресс 😊",
    "В тебе сочетание силы и нежности — идеальное 💖",
    "С тобой уютно даже в дождь ☔️",
    "Ты девочка-магия — всё получается ✨",
    "Твои глаза — как космос, хочется в них пропасть 🌌",
    "Твой смех лечит лучше любого чая 🍵",
    "Ты делаешь этот чат теплее 🧸",
    "С тобой даже тильт улыбается 😌",
    "Кто сегодня самая очаровательная? Правильно — ты 💅",
    "Ты вдохновляешь двигаться дальше 🚀",
    "Твоё сердце — дом для нежности 🏡",
    "Ты из тех, чьё «просто» — уже прекрасно 🌷",
    "Даже если день сложный — ты всё равно супер ⭐️",
    "С тобой хочется творить и радоваться 💐",
    "Ты — уютный плед в этом мире 🧶",
    "Твой вайб — чистый serotonin boost 🎧",
    "Мир стал лучше, когда ты сюда пришла 🤍",
    "Ты будто из лучшего сна — и это реальность 🌙",
    "Твой стиль — отдельная форма искусства 🎨",
    "Ты умеешь согреть одним сообщением 🔥",
    "Ты — одно большое «вау» 💫",
    "Ты делаешь будни похожими на праздник 🎈",
    "С тобой рядом спокойнее и светлее 🌞",
    "Ты — нежность в человеческом виде 🫶",
    "Космос завидует твоей красоте 🌠",
    "Ты — та, на кого хочется равняться 🌿",
    "Ты сияешь даже без хайлайтера ✨",
    "Ты прекрасна без «но» и «если» 💌",
    "Ты — лучшая версия себя, просто продолжай 💎",
    "Ты — наша гордость и любовь 💗",
    "Твоя доброта — редкость и сокровище 🗝️",
    "Ты — главная девочка этого дня 👑",
    "Ты делаешь мир уютнее одним присутствием 🫧",
    "С тобой любое дело становится проще 🧩",
    "Ты всегда чуть красивее, чем вчера 🌺",
    "Ты — просто блеск! ✨",
    "Ты — заряд милоты на неделю 🐣",
    "Ты — наш маленький шедевр 🎨",
    "Ты — витамин радости группы A 💊",
]

async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = update.effective_user
    ensure_user(me.id, me.first_name, me.username)

    if context.args:
        target = context.args[0]
        await update.message.reply_text(f"{random.choice(COMPLIMENTS)} {target}")
        return

    pool = [uid for uid in state.get("known_users", []) if uid != me.id]
    if not pool:
        await update.message.reply_text(random.choice(COMPLIMENTS))
        return
    target_id = random.choice(pool)
    await update.message.reply_text(f"{random.choice(COMPLIMENTS)} {display_user(target_id)}", parse_mode="HTML")

# ===================== ЛЕСБИ-ПАРА (из всех известных) =====================
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pool = list(set(state.get("known_users", [])))
    if len(pool) < 2:
        await update.message.reply_text("Недостаточно участниц для пары")
        return

    if state["last_lesbi_date"] == today_str() and state.get("last_lesbi_pair"):
        a, b = state["last_lesbi_pair"]
        await update.message.reply_text(
            f"👭 Пара дня уже выбрана: {display_user(a)} + {display_user(b)} 💞",
            parse_mode="HTML"
        )
        return

    a, b = random.sample(pool, 2)
    state["last_lesbi_date"] = today_str()
    state["last_lesbi_pair"] = [a, b]
    save_state()

    lines = [
        "🌈 Сегодняшняя лесби-пара: {a} и {b} 💋",
        "🫶 Кто бы мог подумать! {a} и {b} — пара дня!",
        "💘 Амур попал точно в цель! {a} и {b} теперь вместе 😍",
        "💞 Любовь витает в воздухе: {a} + {b} = ❤️",
    ]
    msg = random.choice(lines).format(a=display_user(a), b=display_user(b))
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

# ===================== /role @юзер =====================
ROLES = [
    "самая красивая девочка💖",
    "самая милая киска😺",
    "самая нежная принцесса🌸",
    "самая грустная пельмешка😔",
    "самая сияющая звёздочка✨",
    "самая злая ведьмочка🧙‍♀️",
    "самая модная иконка👠",
    "самая загадочная душа🌀",
    "самая радужная булочка🌈",
    "самая одинокая тучка🌧",
    "какашка дня💩",
    "бунтарка чата🔥",
    "психованная фея🤯",
    "плакса дня😭",
    "драмаквин вечера👑",
    "самая громкая жаба🐸",
    "киска с характером🐾",
    "королева спама📱",
    "самая непредсказуемая🎲",
    "девочка вайба🎧",
    "самая эстетичная на районе🎨",
    "инста-дива дня📸",
    "самая поющая в душе🎤",
    "самая секси в пижаме💃",
    "королева вечеринки🎉",
    "девочка с космосом в глазах🌌",
    "богиня флирта💋",
    "дева хаоса🫦",
    "секретный агент чата🕵️‍♀️",
    "персик дня🍑",
    "кошмар всех бывших💔",
    "кофейная богиня☕️",
    "самая громкая ржунька😂",
    "девочка-сюрприз🎲",
    "случайный гений🧠",
    "ловушка для сердец❤️‍🔥",
    "обнимашка на ножках🤗",
    "самая ранимая душа🥺",
    "носик-кнопочка дня👃",
    "девочка, которой хочется чай налить🍵",
    "сердце на распашку💘",
    "сладость с начинкой из грусти🍬",
    "облако нежности☁️",
    "милашка дня🧸",
    "тёплый плед среди шторма🫂",
    "улыбка, за которую прощаешь всё😊",
    "девочка-обнимашка🤍",
    "самая драматичная🎭",
    "капризуля дня😈",
    "девочка с планом (и бартером)📋",
    "высшая лига феминизма🧜‍♀️",
    "та, кто делает мозги🥴",
    "шальная императрица👑",
    "главная звезда чата🌟",
    "самая занятная интриганка🧩",
    "девочка с короной по умолчанию👸",
    "фея с бдсм-крыльями🧚‍♀️",
    "заколдованная котлетка🍖",
    "волшебница уютных вечеров🌙",
    "мистическая богиня сна😴",
    "ведьма на минималках🧙‍♀️",
    "ведьма, которая не варит борщ🧹",
    "девочка-зелье🧪",
    "та, что танцует под луной💃",
    "девочка-ой-всё🙄",
    "пиписка на каблуках🍆",
    "грустный котик в теле стервы😿",
    "та, что не отвечает🙅‍♀️",
    "кринж-королева🫠",
    "шарик тревожности🎈",
    "хитрая жопка🍑",
    "пустое место💨",
    "позор клана🤡",
    "ошибка природы⚠️",
    "фиаско дня📉",
    "ходячий кринж🫠",
    "минус в карму👎",
    "неудача недели💀",
    "хз кто и зачем тут🙃",
    "причина стыда сегодня😬",
    "баг в матрице🕳",
    "главный повод для фейспалма🤦‍♀️",
    "самая бесячая🧿",
    "фейл века😵",
    "анти-звезда чата🚫",
    "проклятие дня🧟‍♀️",
    "катастрофа в юбке🌪",
    "повод выйти из чата🚪",
    "фоновый шум🔇",
    "глюк системы🖥",
    "недоразумение с вайбом😵‍💫",
    "рандомная npc💻",
    "баг с лицом🫥",
    "урон по глазам👁",
    "та, кого лучше не вспоминать👻",
    "моральный вирус🦠",
    "сомнительная личность🕳",
    "бан без суда и следствия🚷"
]

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Используй: /role @username")
        return
    raw = context.args[0]
    target = raw if raw.startswith("@") else ("@" + raw)
    await update.message.reply_text(f"{target} сегодня {random.choice(ROLES)}")

# ===================== ДЕНЬ РОЖДЕНИЯ (ежедневная проверка) =====================
def _parse_day_month(bday: str):
    """Возвращает (day, month) если удалось, иначе None."""
    if not bday:
        return None
    bday = bday.strip()
    for fmt in ("%d.%m.%Y", "%d.%m"):
        try:
            dt = datetime.strptime(bday, fmt)
            return dt.day, dt.month
        except Exception:
            pass
    return None

async def birthday_job(context: ContextTypes.DEFAULT_TYPE):
    today = date.today()
    for suid, u in state["users"].items():
        dm = _parse_day_month(u.get("bday", ""))
        if not dm:
            continue
        d, m = dm
        if d == today.day and m == today.month:
            name = u.get("name") or display_user(int(suid))
            text = f"🎂 Сегодня день рождения у {name}! Пожелаем счастья, любви и побед! 🥳"
            try:
                await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Не удалось отправить поздравление: {e}")

# ===================== РЕГИСТРАЦИЯ И ЗАПУСК =====================
def build_application():
    app = ApplicationBuilder().token(TOKEN).build()

    # Приветствия новых
    app.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))

    # Профиль (пошагово) — добавляем раньше, чем трекер сообщений
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("editprofile", editprofile)],
        states={
            STEP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_name)],
            STEP_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nick)],
            STEP_UID:  [MessageHandler(filters.TEXT & ~filters.COMMAND, step_uid)],
            STEP_BDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_bday)],
            STEP_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_city)],
            STEP_TIKTOK: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_tiktok)],
            STEP_QUOTE: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_quote)],
        },
        fallbacks=[],
    )
    app.add_handler(edit_conv)
    app.add_handler(CommandHandler("profile", profile))

    # Базовые команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("rules", rules))

    # Фан
    app.add_handler(CommandHandler("pipisa", pipisa))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("predskaz", predskaz))
    app.add_handler(CommandHandler("hugs", hugs))
    app.add_handler(CommandHandler("compliment", compliment))
    app.add_handler(CommandHandler("lesbi", lesbi))
    app.add_handler(CommandHandler("role", role))

    # Трекер сообщений (последним — чтобы не сбивать ConversationHandler)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_speaker))

    # JobQueue — поздравления с ДР (каждое утро в 09:00 по времени сервера)
    app.job_queue.run_daily(birthday_job, time(hour=9, minute=0))

    return app

if __name__ == "__main__":
    application = build_application()
    print("OnlyGirls bot запущен…")
    application.run_polling()
