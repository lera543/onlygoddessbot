# -*- coding: utf-8 -*-
import json
import logging
import random
import re
from datetime import datetime, date, time
from pathlib import Path

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ChatMemberHandler,
    ConversationHandler, ContextTypes, filters
)

# ===================== НАСТРОЙКИ =====================
TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863
DATA_FILE = Path("data.json")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("OnlyGirlsBot")

# ===================== ХРАНИЛИЩЕ =====================
state = {
    "users": {},            # { user_id(str): {...} }
    "known_users": [],      # [int, ...]
    "last_lesbi_date": None,
    "last_lesbi_pair": None
}

def load_state():
    if DATA_FILE.exists():
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            state.update(data)
            for suid, u in state.get("users", {}).items():
                u.setdefault("name", "")
                u.setdefault("username", "")
                u.setdefault("nickname", "")
                u.setdefault("uid", "")
                u.setdefault("bday", "")
                u.setdefault("city", "")
                u.setdefault("tiktok", "")
                u.setdefault("joined_date", "")
                u.setdefault("quote", "")
                u.setdefault("pipisa", 0.0)
                u.setdefault("pipisa_power", 0)
                u.setdefault("last_pipisa", None)
                u.setdefault("last_prediction", None)
                u.setdefault("last_duel_date", None)
                u.setdefault("duel_uses", 0)
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

def ensure_user(user_id: int):
    suid = str(user_id)
    if suid not in state["users"]:
        state["users"][suid] = {
            "name": "",
            "username": "",
            "nickname": "",
            "uid": "",
            "bday": "",
            "city": "",
            "tiktok": "",
            "joined_date": "",
            "quote": "",
            "pipisa": 0.0,
            "pipisa_power": 0,
            "last_pipisa": None,
            "last_prediction": None,
            "last_duel_date": None,
            "duel_uses": 0,
        }
    if user_id not in state.get("known_users", []):
        state["known_users"].append(user_id)

def tg_link_from_id(user_id: int, text: str = "девочка") -> str:
    return f'<a href="tg://user?id={user_id}">{text}</a>'

def display_user(user_id: int) -> str:
    u = state["users"].get(str(user_id))
    if u:
        if u.get("name"):
            return u["name"]
        if u.get("username"):
            return f"@{u['username']}"
    return tg_link_from_id(user_id, "девочка")

def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")

def find_user_id_by_username(username: str):
    username = username.lower().lstrip("@")
    for suid, u in state["users"].items():
        if u.get("username") and u["username"].lower() == username:
            return int(suid)
    return None

def store_user(user):
    if not user:
        return
    ensure_user(user.id)
    u = state["users"][str(user.id)]
    u["name"] = user.mention_html()
    if user.username:
        u["username"] = user.username
    save_state()

# убрать пробел перед эмодзи
_EMOJI_SPACE_FIX_RE = re.compile(r' (?=[\u2600-\u27BF\U0001F300-\U0001FAFF])')
def emo(s: str) -> str:
    return _EMOJI_SPACE_FIX_RE.sub("", s)

# ===================== КЛАВА =====================
MAIN_KB = ReplyKeyboardMarkup(
    [
        ["🌱 /pipisa", "🔮 /predskaz", "💐 /compliment"],
        ["🤗 /hugs", "🌈 /lesbi", "🏷️ /role"],
        ["⚔️ /duel", "🏆 /top5", "📊 /rating"],
        ["👤 /profile", "✏️ /editprofile"],
        ["📜 /rules", "ℹ️ /info", "🙈 /hide"]
    ],
    resize_keyboard=True
)

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(emo("Меню открыто💖"), reply_markup=MAIN_KB)

async def hide(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(emo("Спрятала клавиатуру🙈"), reply_markup=ReplyKeyboardRemove())

# ===================== ПРИВЕТСТВИЕ/ПРОЩАНИЕ =====================
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    old = cmu.old_chat_member.status
    new = cmu.new_chat_member.status
    if (old in ("left", "kicked")) and (new in ("member", "administrator", "creator")):
        user = cmu.new_chat_member.user
        store_user(user)
        text = (
            f"Добро пожаловать, {user.mention_html()}❣️"
            f' Ознакомься пожалуйста с правилами клана'
            f' (<a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a>)🫶'
            f" Важная информация всегда в закрепе❗️ Клановая приставка: ঔ"
        )
        await context.bot.send_message(chat_id=cmu.chat.id, text=emo(text), parse_mode="HTML")

async def farewell_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    old = cmu.old_chat_member.status
    new = cmu.new_chat_member.status
    if (old in ("member", "administrator", "creator")) and (new in ("left", "kicked")):
        user = cmu.old_chat_member.user
        store_user(user)
        text = f"{display_user(user.id)} покинула чат, будем скучать💔"
        await context.bot.send_message(chat_id=cmu.chat.id, text=emo(text), parse_mode="HTML")

# по сервис-сообщениям (надёжнее)
async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.new_chat_members:
        return
    for m in update.message.new_chat_members:
        store_user(m)
        text = (
            f"Добро пожаловать, {m.mention_html()}❣️"
            f' Ознакомься пожалуйста с правилами клана'
            f' (<a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a>)🫶'
            f" Важная информация всегда в закрепе❗️ Клановая приставка: ঔ"
        )
        await context.bot.send_message(chat_id=update.effective_chat.id, text=emo(text), parse_mode="HTML")

async def goodbye_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.left_chat_member:
        return
    u = update.message.left_chat_member
    store_user(u)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=emo(f"{display_user(u.id)} покинула чат, будем скучать💔"),
        parse_mode="HTML"
    )

# ===================== /START и /ABOUT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(
        emo("Привет!Я — Мать Богинь для клана OnlyGirls💖 Напиши /about чтобы узнать мои команды."),
        reply_markup=MAIN_KB
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(emo(
        "✨ Команды:\n"
        "/menu — открыть клавиатуру\n"
        "/editprofile — заполнить/обновить профиль(пошагово)\n"
        "/profile — показать твой профиль\n"
        "/pipisa — вырастить/уменьшить пипису(1 раз в день, минимум −50 см)\n"
        "/duel @юзер — дуэль пипис(до 3 в день, сила растёт)\n"
        "/top5 — топ-5 по пиписе\n"
        "/rating — полный рейтинг пипис\n"
        "/predskaz — предсказание дня(1 раз в день)\n"
        "/compliment [@юзер] — комплимент тебе/указанной\n"
        "/hugs [@юзер] — обнимашки(для всех/указанной)\n"
        "/lesbi — лесби-пара дня(1 раз в день)\n"
        "/role [@юзер] — «кто сегодня самая…»\n"
        "/rules — правила клана(ссылка)\n"
        "/info — актуальная инфа(ссылка)\n"
        "/hide — убрать клавиатуру"
    ))

# ===================== /RULES и /INFO =====================
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(
        emo('Котик, правила клана <a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a>🫶'),
        parse_mode="HTML"
    )

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    text = '<a href="https://telegra.ph/Aktualnaya-informaciya-08-21">Здесь</a> актуальная информация по клану, кастомкам и т.д🖤'
    await update.message.reply_text(emo(text), parse_mode="HTML", disable_web_page_preview=True)

# ===================== ПРОФИЛЬ =====================
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
    store_user(update.effective_user)
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"].get(uid)
    await update.message.reply_text(emo(render_profile(u)), parse_mode="HTML")

async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    ensure_user(update.effective_user.id)
    context.user_data["profile_answers"] = {}
    await update.message.reply_text("Как тебя зовут?\n(имя)")
    return STEP_NAME

async def step_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["name"] = update.effective_user.mention_html()
    await update.message.reply_text("Какой у тебя ник в игре?")
    return STEP_NICK

async def step_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["nickname"] = update.message.text.strip()
    await update.message.reply_text("Какой у тебя UID?")
    return STEP_UID

async def step_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["uid"] = update.message.text.strip()
    await update.message.reply_text("Когда у тебя день рождения?\n(например, 01.01.2000 или 01.01)")
    return STEP_BDAY

async def step_bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["bday"] = update.message.text.strip()
    await update.message.reply_text("Из какого ты города?")
    return STEP_CITY

async def step_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["city"] = update.message.text.strip()
    await update.message.reply_text("Оставь ссылку на TikTok или просто свой ник\n(@username):")
    return STEP_TIKTOK

async def step_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["tiktok"] = update.message.text.strip()
    await update.message.reply_text("Поделись своим девизом или любимой цитатой:")
    return STEP_QUOTE

async def step_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["quote"] = update.message.text.strip()
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    stored = state["users"][uid]
    for k, v in context.user_data["profile_answers"].items():
        stored[k] = v
    if not stored.get("joined_date"):
        stored["joined_date"] = today_str()
    stored["username"] = (update.effective_user.username or "").lower()
    save_state()
    await update.message.reply_text("Профиль обновлён ✅")
    return ConversationHandler.END

# ===================== ПИПИСА =====================
PIPISA_UP_REACTIONS = [
    "Она стремится к вершинам!📈",
    "Вперед и выше — гордимся!🥳",
    "Так растёт только легенда!🌟",
    "Сияет и радует хозяйку!✨"
]
PIPISA_DOWN_REACTIONS = [
    "Ничего, завтра вернём позиции💪",
    "Иногда и героям нужен отдых🌧️",
    "Обнимем — и всё пройдёт🫂",
    "Сменим вайб — пойдёт вверх🌈"
]

def _rand_delta():
    d = round(random.uniform(-10.0, 10.0), 1)
    if abs(d) < 0.1:
        d = 0.1 if random.random() > 0.5 else -0.1
    return d

async def pipisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]
    u["username"] = (update.effective_user.username or "").lower()
    if u.get("last_pipisa") == today_str():
        await update.message.reply_text("Пипису можно растить/мерить только раз в день!🌱")
        return
    delta = _rand_delta()
    new_val = round(float(u.get("pipisa", 0.0)) + delta, 1)
    new_val = max(new_val, -50.0)
    u["pipisa"] = new_val
    u["last_pipisa"] = today_str()
    save_state()
    if delta > 0:
        phrase = random.choice([
            f"🍆 Твоя пиписа выросла на {delta:.1f} см!\n{random.choice(PIPISA_UP_REACTIONS)}\nТеперь: {new_val:.1f} см.",
            f"🍆 Ого! +{delta:.1f} см — вот это рост!\n{random.choice(PIPISA_UP_REACTIONS)}\nТекущий размер: {new_val:.1f} см."
        ])
    else:
        phrase = random.choice([
            f"🍆 Оу… пиписа уменьшилась на {abs(delta):.1f} см.\n{random.choice(PIPISA_DOWN_REACTIONS)}\nСейчас: {new_val:.1f} см.",
            f"🍆 Немного просела ({abs(delta):.1f} см).\n{random.choice(PIPISA_DOWN_REACTIONS)}\nТекущий размер: {new_val:.1f} см."
        ])
    await update.message.reply_text(emo(phrase), parse_mode="HTML")

# ===================== ДУЭЛЬ (до 3/день, сила) =====================
async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    me = update.effective_user
    ensure_user(me.id)
    state["users"][str(me.id)]["username"] = (me.username or "").lower()
    target_id = None
    if update.message and update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        arg = context.args[0].strip().lstrip("@")
        target_id = find_user_id_by_username(arg)
    if not target_id:
        await update.message.reply_text("Отметь соперницу: /duel @username или ответь на её сообщение командой /duel.")
        return
    if target_id == me.id:
        await update.message.reply_text("С собой дуэлиться нельзя🙃")
        return
    ensure_user(target_id)
    me_u = state["users"][str(me.id)]
    tg_u = state["users"][str(target_id)]
    if me_u.get("last_duel_date") != today_str():
        me_u["last_duel_date"] = today_str()
        me_u["duel_uses"] = 0
    if me_u["duel_uses"] >= 3:
        await update.message.reply_text("Ты уже провела 3 дуэли сегодня. Попробуй завтра🌙")
        return
    my_power = int(me_u.get("pipisa_power", 0))
    opp_power = int(tg_u.get("pipisa_power", 0))
    win_chance = 0.50 + 0.05 * (my_power - opp_power)
    win_chance = max(0.20, min(0.80, win_chance))
    amount = round(random.uniform(0.1, 3.0), 1)
    win = (random.random() < win_chance)
    me_size = float(me_u.get("pipisa", 0.0))
    tg_size = float(tg_u.get("pipisa", 0.0))
    if win:
        steal = min(amount, tg_size + 50.0)
        me_u["pipisa"] = round(me_size + steal, 1)
        tg_u["pipisa"] = round(tg_size - steal, 1)
        me_u["pipisa_power"] = me_u.get("pipisa_power", 0) + 2
        tg_u["pipisa_power"] = tg_u.get("pipisa_power", 0) + 1
        me_u["pipisa"] = max(me_u["pipisa"], -50.0)
        tg_u["pipisa"] = max(tg_u["pipisa"], -50.0)
        outcome = (
            f"⚔️ {me.mention_html()} победила в дуэли у {display_user(target_id)}!\n"
            f"🍆 Перешло {steal:.1f} см → теперь у тебя {me_u['pipisa']:.1f} см, у соперницы {tg_u['pipisa']:.1f} см."
        )
        tail = random.choice(["Легенда усилилась!💪","Сила растёт — берегитесь!✨","Очень опасная богиня…👑"])
    else:
        steal = min(amount, me_size + 50.0)
        me_u["pipisa"] = round(me_size - steal, 1)
        tg_u["pipisa"] = round(tg_size + steal, 1)
        me_u["pipisa_power"] = me_u.get("pipisa_power", 0) + 1
        tg_u["pipisa_power"] = tg_u.get("pipisa_power", 0) + 2
        me_u["pipisa"] = max(me_u["pipisa"], -50.0)
        tg_u["pipisa"] = max(tg_u["pipisa"], -50.0)
        outcome = (
            f"⚔️ {me.mention_html()} проиграла дуэль {display_user(target_id)}...\n"
            f"🍆 Ушло {steal:.1f} см → теперь у тебя {me_u['pipisa']:.1f} см, у соперницы {tg_u['pipisa']:.1f} см."
        )
        tail = random.choice(["Ничего, завтра реванш!🫶","Обнимашки и вперёд к победам🤗","Опыт тоже сила!🌟"])
    me_u["duel_uses"] += 1
    save_state()
    await update.message.reply_text(emo(outcome + "\n" + tail), parse_mode="HTML")

# ===================== РЕЙТИНГИ =====================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)[:5]
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще🌱")
        return
    text = "🏆 ТОП-5 пипис клана:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or tg_link_from_id(int(uid), uid)}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(emo(text), parse_mode="HTML")

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще🌱")
        return
    text = "📊 Полный рейтинг пипис:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or tg_link_from_id(int(uid), uid)}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(emo(text), parse_mode="HTML")

# ===================== 200 ПРЕДСКАЗАНИЙ =====================
PREDICTIONS = [
    # 1–100 — жизнь/настроение
    "Сегодня твой день — даже если облачно☁️","Улыбка решит больше, чем кажется😊","Делай по любви — и будет кайф💖","Вселенная сегодня на твоей стороне✨","Ты видишь больше, чем другие — доверься себе👁️","Маленький шаг тоже движение вперёд👣","Слухи остаются слухами — будь выше🕊️","Пусть душа сегодня потанцует💃","Ты — чьё-то «повезло»🍀","Скажи себе «молодец» — ты это услышишь🥰","Спокойствие — твоя суперсила сегодня🧘‍♀️","Выбери доброту — это заметят🌷","Новость дня будет приятной📨","Пей воду и сияй как бриллиант💎","Случайный комплимент изменит настроение🌈","Твоя интуиция права — доверься ей🔮","Сегодня лучше не спешить — ритм найдётся сам🎵","Поймай луч солнца и улыбнись☀️","Надень любимое — мир подыграет тебе👗","Кто-то тайно тобой восхищается👀","Скажи «нет» лишнему — почувствуешь свободу🕊️","Скажи «да» себе — почувствуешь силу⚡️","Найди красивое в мелочах — в этом магия✨","Сделай паузу — вдох-выдох и дальше🌬️","Хорошая мысль найдёт тебя за чаем🍵","Ты важна для людей больше, чем думаешь💞","Сегодня легко получится то, что откладывала✅","Сделай фото — поймаешь момент дня📸","Вспомни мечту и приблизь её на 1 шаг🚶‍♀️","Слова доброты вернутся тебе эхом📡","Убирайся под музыку — и мысли тоже разложатся🧹","Сегодня день лёгких совпадений🔗","Ты слышишь себя громче, чем шум вокруг🔊","Полюби свой темп — он правильный⌛️","Интернет подкинет полезную идею💡","Дай место чуду — оно любит простор🌌","Твоя энергия исцеляет других🌿","Сделай приятность без повода — вернётся сторицей🎁","Ничего не сломано — всё в процессе🛠","Твои дела под контролем — даже если не кажется🧭","День удачных диалогов — говори честно💬","Улыбнись зеркалу — оно союзник🪞","Доверяй тихим чувствам — они точны🎯","Кофе сегодня особенно волшебный☕️","Не сравнивай — у тебя своя траектория🚀","Музыка дня найдёт тебя сама🎧","Слова благодарности откроют дверь🚪","Мягкость — не слабость, а сила🤍","Не трать энергию на ненужные споры🙅‍♀️","Тебя ждёт маленькая радость в пути🛤","Заметишь знак — он для тебя🪄","Твоя доброта кому-то сегодня очень нужна🤝","Случайная встреча согреет сердце🔥","Запусти мини-ритуал заботы о себе🛁","Сон подскажет ответ сегодня ночью🌙","Ты достаточно — прямо сейчас💫","Не бойся попросить помощи — это мудро🧠","Сделай шаг в неизвестность — там интересно🗺","Сегодня легче, чем ты думаешь🎈","Твоя улыбка сегодня кому-то спасёт день🛟","Ты светишься изнутри — заметно всем⭐️","Смени обои на телефоне — вместе сменится вайб📱","Разгрузи сумку и голову — станет легче🎒","Любимое блюдо подарит силы🍲","Самая красивая мысль придёт в дороге🚌","Ты умеешь больше, чем признаёшься себе🏅","Список дел сократится сам — доверяй потоку🌊","Отложи тяжёлое до завтра — сегодня ласка🌸","Спрячься в плед — мир подождёт🫶","Скажи «спасибо» себе — это важно🎀","Сегодня слова ложатся мягко — используй их мудро📝","Твоё сердце знает дорогу домой🏡","Чудо уже выехало — останется только открыть дверь🚪","День для маленьких побед — собери коллекцию🏆","Ты магнит для хороших новостей📩","Мир не против тебя — он за тебя🤍","Ждать не страшно, страшно не мечтать🌠","Смелая мысль найдёт тебя первой🗯","Твоя внутренняя девочка хочет печеньку🍪","Ты причина чьей-то надежды сегодня🌟","Обними себя — и станет теплее🫂","Вдох вдохновит кого-то рядом💨","Ты важнее дедлайнов❤️","Тишина сегодня лечит лучше слов🤫","У тебя получится то, что казалось сложным🏔","Высыпаться — тоже успех😴","Запиши мечту — так она ближе🖊️","Смейся чаще — это магия😂","Твой голос важен — говори честно🎙️","Подари себе 10 минут без телефона📵","Сегодня тебя полюбит случайность🎲","Разреши себе отдых без чувства вины🛌","Скажи «я могу» — и делай можное✨","Твои границы — святое🛡️","Сходи на свет — там легче☀️","Красивое рядом — просто оглянись👀","С тобой безопасно — это ценят🫶","Ты достойна лучшего — по умолчанию👑","Ласковые слова к себе — обязательны сегодня💗","Вдохни глубоко — мир не спешит🌍","Твоя мягкость делает мир добрее🧸","С тобой всё ок — правда👌",
    # 101–150 — красота/самооценка
    "Красота начинается с принятия себя😍","Твоё лицо любит воду и сон — побалуй его💧","Твои глаза сияют даже без хайлайтера✨","Твоя улыбка — лучший аксессуар💋","Твоя кожа любит нежность — будь мягче с собой🫧","Красота — это твоё настроение, а не макияж🎨","Ты красива, когда веришь себе💖","Самое красивое в тебе — живость и огонь🔥","Тебе идёт смелость и честность💫","Твоя походка — как музыка, не останавливайся🎶","Пусть волосы сегодня танцуют — и ты вместе с ними💃","Губы помнят комплименты — скажи их себе💌","Зеркало сегодня твой фан-клуб📣","Ты шедевр в любой одежде🖼","Твоему стилю достаточно твоего вкуса👗","Нежность — твой естественный хайлайтер🌟","Ты не обязана быть идеальной, чтобы быть прекрасной🌷","Каждая твоя черта — история, а не недостаток📚","Улыбнись глазами — мир растает🧊","Твои руки создают тепло — и это видно🤲","Красота — это как ты заботишься о себе🫶","Лучи комплиментов летят к тебе — не уворачивайся💫","Ты сияешь, когда спокойна🕊️","Тебе идёт уверенность — носи её, как корону👑","Твой смех — украшение дня🎀","Лёгкий румянец счастья — лучший макияж🌺","Твой профиль — как нежная линия горизонта🌅","Тебе идёт твоя уникальность🧩","Ты — эталон для самой себя🏵","Твои ресницы держат секреты звёзд✨","Грация в каждом твоём движении🦢","У тебя идеальная для тебя фигура💖","Твой взгляд умеет говорить громче слов👁️","Волосы любят твоё внимание — дай им ласку🪮","Красота в твоей заботе о себе🌷","Ты — эстетика настоящего момента🪞","Ты нравишься себе — и это видно🌈","Твоя мимика — живопись радости🎨","Честность украшает тебя больше бликов✨","Ты прекрасна — и точка❤️","Твоё «я» — главная изюминка🍒","Твоё настроение — лучший парфюм🫶","Ты нежно красива даже без усилий🌸","Твоя осанка — стих о достоинстве📜","Любовь к себе на тебе сидит идеально🤍","Ты — картинка «до» и «после» одновременно🌗","Ты умеешь быть роскошной без повода💎","Сияй так, как тебе удобно🌟","Твоя мягкость — это суперкрасиво🤍","Ты — сама эстетика утра☀️","Ты — та самая девочка-муза🎻",
    # 151–200 — мотивация/самомотивация
    "Начни с малого — важно начинать🚪","Сделай сегодня на один шаг больше🏃‍♀️","Твои цели реальны — проверь действием✅","Доводи до конца — там конфетти🎊","План на один час творит чудеса🗓","Сначала сделай, потом сомневайся🪄","Меняй по 1% в день — и горы подвинутся⛰️","Спроси себя: что я могу сейчас?🔧","Сомнения шумят, но рулят действия🚗","Ресурс важнее скорости — береги себя🧡","Сделай черновик — это уже движение✍️","Прогресс > перфекционизм📈","Разреши себе делать неидеально👌","Выбирай простое действие — и вперёд➡️","Расставь приоритеты — и станет легче🧭","Собери себя ласково и начни🧩","Награди себя за маленький шаг🍫","Двигайся тихо, но стабильно🔁","Спроси о помощи — это ускоряет🤝","Отказ — тоже опыт, а опыт — сила🧠","Делай то, что контролируешь, и отпусти остальное🌬️","Смена фокуса — новый результат🎯","Запланируй отдых так же, как задачи🛏","Сохраняй ритм — темп придёт сам🥁","Готовься меньше, делай больше⚙️","Настроение догонит действие🏃‍♀️","Твои решения создают будущее🧱","Не сравнивай первый шаг с чьим-то сотым📊","Отмечай прогресс, а не ошибки📌","Неразбиваемые дедлайны — мягкие, но реальные🧵","Твоя дисциплина — нежная, а не жестокая🫶","План B — не поражение, а мудрость🧠","Тебе можно отдохнуть и вернуться сильнее💪","Сделай «микро-дело» прямо сейчас🕐","Страх уйдёт, когда увидит тебя в деле🦁","Даже 10 минут — вклад в мечту⏱","Сохраняй обещания себе — это уважение🤍","Сконцентрируйся на текущем шаге👣","Маленькая победа — топливо для следующей⛽️","Добавь игры в задачу — будет легче🎮","Сомнения — шум, твоя цель — музыка🎧","Запиши результат, который хочешь — и действуй🖊️","Если тяжело — снизь уровень сложности🔽","Твоя стойкость мягкая, но упрямая🌱","Паузы — часть процесса, не сдавайся⏸","Не бойся менять план, если меняешься ты🔁","Ты — система, а не одно событие🧩","Сохраняй любопытство — оно ведёт дальше🔎","Начни — и станет понятно, как продолжить➡️","Будь терпелива к себе — путь долгий, но твой🛤"
]

async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]
    if u.get("last_prediction") == today_str():
        await update.message.reply_text("🔮 Предсказание уже было сегодня!")
        return
    u["last_prediction"] = today_str()
    save_state()
    text = f"🔮 {random.choice(PREDICTIONS)}"
    await update.message.reply_text(emo(text))

# ===================== КОМПЛИМЕНТЫ =====================
COMPLIMENTS = [
    "Ты как солнечный луч — теплее с тобой☀️","Твой смех лечит лучше таблеток😂","С тобой хочется быть настоящей🤍",
    "Ты умеешь красиво жить и чувствовать🌷","Твоя доброта — редкая суперсила💫","Ты заряжаешь спокойствием🕊️",
    "С тобой уютно как под пледом🧸","Твоё мнение важно и ценится📝","Ты украшаешь любое место, где появляешься✨",
    "Ты слышишь между строк — это талант🎧","С тобой легко говорить честно💬","Ты как глоток холодной воды летом💧",
    "Ты делаешь дни мягче🫶","Ты из тех, кому доверяют тайны🔒","Твоя улыбка — мой фаворит сегодня💖",
    "Ты вдохновляешь быть лучше каждый день🌟","У тебя красивое чувство такта🎻","Ты делаешь мир нежнее🤍",
    "Ты очень бережно относишься к людям — это видно🤲","У тебя шикарное чувство юмора🤣",
    "Ты словно маяк — рядом безопасно🛟","Ты умеешь радоваться за других — это редкость🎁",
    "Ты слышишь себя — и это восхищает🎯","Ты настоящая, и это прекрасно🌸",
    "Твои слова могут быть домом🏡","С тобой хочется делиться хорошим📩",
    "Ты светлая девочка, спасибо, что ты есть⭐️","Ты красивая без условий и сравнений👑",
    "Ты заметная, даже когда молчишь🪄","Ты бережно держишь свои границы — горжусь🛡️",
    "Ты умеешь поддержать одним взглядом👀","Ты очень стильная, даже когда в пижаме👗",
    "Ты вдохновляешь на добрые поступки💝","Ты делаешь этот чат живым🎉",
    "Ты как утро — свежая и нежная🌅","Ты красиво злишься — с достоинством🦢",
    "Ты даёшь чувство «со мной всё ок»👌","Ты тонкая, но сильная одновременно🦋",
    "Ты важная девочка для этого мира🌍","Ты — маленькая вселенная, и это видно🌌"
]

def pick_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.reply_to_message:
        return update.message.reply_to_message.from_user.id
    if context.args:
        who = context.args[0].lstrip("@")
        return find_user_id_by_username(who)
    # рандом из known_users, кроме себя
    me = update.effective_user.id
    pool = [uid for uid in state.get("known_users", []) if uid != me]
    return random.choice(pool) if pool else None

async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    ensure_user(update.effective_user.id)
    tid = pick_target_user(update, context)
    if not tid:
        await update.message.reply_text("Кому комплимент? Ответь на сообщение или укажи /compliment @username.")
        return
    store_user(update.effective_user)
    text = f"{display_user(update.effective_user.id)} говорит {display_user(tid)}: {random.choice(COMPLIMENTS)}"
    await update.message.reply_text(emo(text), parse_mode="HTML")

# ===================== HUGS =====================
HUGS_POOL = [
    "🤗 {a} крепко обняла {b} — тепло доставлено по адресу🧸",
    "💞 {a} нежно прижалась к {b} — пусть тревоги тают🌷",
    "🥰 {a} согрела {b} своими обнимашками — зарядилась любовью!",
    "🫶 {a} и {b} — сегодня самый милый дуэт!",
    "Кто не обнимется — тот не играет в кастомке!",
    "🫂 Токсиков тоже иногда обнимают… по голове… табуреткой🙃",
    "Передаю мягкость, заботу и печеньку🍪 — {a} → {b}",
    "Крепко-крепко и очень нежно — трепещи, грусть!🫂 {a} обняла {b}",
    "Пусть тревоги уменьшаются на 50% после этих объятий🌸 {a} для {b}"
]

async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    me = update.effective_user
    # адресно
    if context.args:
        target = context.args[0]
        msg = random.choice([
            f"🤗 {me.mention_html()} обняла {target}! Тепло доставлено🧸",
            f"💞 {me.mention_html()} отправила объятия {target}. Всё будет хорошо🌷",
        ])
        await update.message.reply_text(emo(msg), parse_mode="HTML")
        return
    # по ответу
    if update.message and update.message.reply_to_message:
        tid = update.message.reply_to_message.from_user.id
        store_user(update.message.reply_to_message.from_user)
        tpl = random.choice(HUGS_POOL)
        a = me.mention_html()
        b = display_user(tid)
        text = tpl.format(a=a, b=b) if ("{a}" in tpl or "{b}" in tpl) else f"{a} обняла {b} — {tpl}"
        await update.message.reply_text(emo(text), parse_mode="HTML")
        return
    # рандом
    pool = [uid for uid in state.get("known_users", []) if uid != me.id]
    if not pool:
        await update.message.reply_text("Обнимашки для всех в чате!🫂")
        return
    tid = random.choice(pool)
    tpl = random.choice(HUGS_POOL)
    a = me.mention_html()
    b = display_user(tid)
    text = tpl.format(a=a, b=b) if ("{a}" in tpl or "{b}" in tpl) else f"{a} обняла {b} — {tpl}"
    await update.message.reply_text(emo(text), parse_mode="HTML")

# ===================== ЛЕСБИ-ПАРА ДНЯ =====================
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    pool = list(set(state.get("known_users", [])))
    if len(pool) < 2:
        await update.message.reply_text("Недостаточно участниц для пары")
        return
    if state["last_lesbi_date"] == today_str() and state.get("last_lesbi_pair"):
        a, b = state["last_lesbi_pair"]
        await update.message.reply_text(
            emo(f"👭 Пара дня уже выбрана: {display_user(a)} + {display_user(b)}💞"),
            parse_mode="HTML"
        )
        return
    a, b = random.sample(pool, 2)
    state["last_lesbi_date"] = today_str()
    state["last_lesbi_pair"] = [a, b]
    save_state()
    lines = [
        "🌈 Сегодняшняя лесби-пара: {a} и {b}💋",
        "🫶 Кто бы мог подумать! {a} и {b} — пара дня!",
        "💘 Амур попал точно в цель! {a} и {b} теперь вместе😍",
        "💞 Любовь витает в воздухе: {a} + {b} =❤️"
    ]
    msg = random.choice(lines).format(a=display_user(a), b=display_user(b))
    await context.bot.send_message(chat_id=update.effective_chat.id, text=emo(msg), parse_mode="HTML")

# ===================== РОЛИ =====================
ROLES = [
    "самая красивая девочка💖","самая милая киска😺","самая нежная принцесса🌸","самая грустная пельмешка😔","самая сияющая звёздочка✨",
    "самая злая ведьмочка🧙‍♀️","самая модная иконка👠","самая загадочная душа🌀","самая радужная булочка🌈","самая одинокая тучка🌧",
    "какашка дня💩","бунтарка чата🔥","психованная фея🤯","плакса дня😭","драмаквин вечера👑","самая громкая жаба🐸","киска с характером🐾",
    "королева спама📱","самая непредсказуемая🎲","девочка вайба🎧","самая эстетичная на районе🎨","инста-дива дня📸","самая поющая в душе🎤",
    "самая секси в пижаме💃","королева вечеринки🎉","девочка с космосом в глазах🌌","богиня флирта💋","дева хаоса🫦","секретный агент чата🕵️‍♀️",
    "персик дня🍑","кошмар всех бывших💔","кофейная богиня☕️","самая громкая ржунька😂","девочка-сюрприз🎲","случайный гений🧠",
    "ловушка для сердец❤️‍🔥","обнимашка на ножках🤗","самая ранимая душа🥺","носик-кнопочка дня👃","девочка, которой хочется чай налить🍵",
    "сердце на распашку💘","сладость с начинкой из грусти🍬","облако нежности☁️","милашка дня🧸","тёплый плед среди шторма🫂",
    "улыбка, за которую прощаешь всё😊","девочка-обнимашка🤍","самая драматичная🎭","капризуля дня😈","девочка с планом (и бартером)📋",
    "высшая лига феминизма🧜‍♀️","та, кто делает мозги🥴","шальная императрица👑","главная звезда чата🌟","самая занятная интриганка🧩",
    "девочка с короной по умолчанию👸","фея с бдсм-крыльями🧚‍♀️","заколдованная котлетка🍖","волшебница уютных вечеров🌙",
    "мистическая богиня сна😴","ведьма на минималках🧙‍♀️","ведьма, которая не варит борщ🧹","девочка-зелье🧪","та, что танцует под луной💃",
    "девочка-ой-всё🙄","пиписка на каблуках🍆","грустный котик в теле стервы😿","та, что не отвечает🙅‍♀️","кринж-королева🫠","шарик тревожности🎈",
    "хитрая жопка🍑","пустое место💨","позор клана🤡","ошибка природы⚠️","фиаско дня📉","ходячий кринж🫠","минус в карму👎","неудача недели💀",
    "хз кто и зачем тут🙃","причина стыда сегодня😬","баг в матрице🕳","главный повод для фейспалма🤦‍♀️","самая бесячая🧿","фейл века😵",
    "анти-звезда чата🚫","проклятие дня🧟‍♀️","катастрофа в юбке🌪","повод выйти из чата🚪","фоновый шум🔇","глюк системы🖥",
    "недоразумение с вайбом😵‍💫","рандомная npc💻","баг с лицом🫥","урон по глазам👁","та, кого лучше не вспоминать👻","моральный вирус🦠",
    "сомнительная личность🕳","бан без суда и следствия🚷"
]

async def role_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    me = update.effective_user
    target_id = None
    if update.message and update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        target_id = find_user_id_by_username(context.args[0])
    else:
        pool = list(set(state.get("known_users", [])))
        if not pool:
            await update.message.reply_text("Некого назначать на роль — чат пустует😿")
            return
        target_id = random.choice(pool)
    ensure_user(target_id)
    text = f"{display_user(target_id)} сегодня {random.choice(ROLES)}"
    await update.message.reply_text(emo(text), parse_mode="HTML")

# ===================== ДР (ежедневно, если в профиле есть bday) =====================
def _parse_day_month(bday: str):
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
            name = u.get("name") or tg_link_from_id(int(suid), "девочка")
            text = f"🎂 Сегодня день рождения у {name}! Пожелаем счастья, любви и побед!🥳"
            try:
                await context.bot.send_message(chat_id=CHAT_ID, text=emo(text), parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Не удалось отправить поздравление: {e}")

# ===================== РЕГИСТРАЦИЯ И ЗАПУСК =====================
def build_application():
    app = ApplicationBuilder().token(TOKEN).build()

    # сервисные привет/пока
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye_member))

    # изменения статуса (резерв)
    app.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(farewell_member, ChatMemberHandler.CHAT_MEMBER))

    # профиль (пошагово)
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

    # базовые
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("hide", hide))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("info", info_cmd))

    # фан/игры
    app.add_handler(CommandHandler("pipisa", pipisa))
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("predskaz", predskaz))
    app.add_handler(CommandHandler("compliment", compliment))
    app.add_handler(CommandHandler("hugs", hugs))
    app.add_handler(CommandHandler("lesbi", lesbi))
    app.add_handler(CommandHandler("role", role_cmd))

    # JobQueue — поздравления с ДР (каждый день в 09:00 по серверу)
    app.job_queue.run_daily(birthday_job, time(hour=9, minute=0))

    return app

if __name__ == "__main__":
    application = build_application()
    print("OnlyGirls bot запущен…")
    application.run_polling(close_loop=False)
