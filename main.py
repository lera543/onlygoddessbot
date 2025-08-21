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
CHAT_ID = -1001849339863  # общий чат
DATA_FILE = Path("data.json")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("OnlyGirlsBot")

# ===================== ХРАНИЛИЩЕ =====================
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
            # мягкая миграция: добавим username там, где нет
            for suid, u in state.get("users", {}).items():
                if "username" not in u:
                    u["username"] = ""
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

def find_user_id_by_username(username: str) -> int | None:
    username = username.lower().lstrip("@")
    for suid, u in state["users"].items():
        if u.get("username") and u["username"].lower() == username:
            return int(suid)
    return None

def store_user(user):
    """Запоминаем красивое имя и username у любого встреченного пользователя."""
    if not user:
        return
    ensure_user(user.id)
    u = state["users"][str(user.id)]
    u["name"] = user.mention_html()
    if user.username:
        u["username"] = user.username
    save_state()

# убираем пробелы ПЕРЕД эмодзи (глобально для всех отправок)
_EMOJI_SPACE_FIX_RE = re.compile(r' (?=[\u2600-\u27BF\U0001F300-\U0001FAFF])')
def emo(s: str) -> str:
    return _EMOJI_SPACE_FIX_RE.sub("", s)

# ===================== КЛАВА =====================
MAIN_KB = ReplyKeyboardMarkup(
    [
        ["🌱 /pipisa", "🔮 /predskaz", "🤗 /hugs"],
        ["🌈 /lesbi", "🏷️ /role", "⚔️ /duel"],
        ["🏆 /top5", "📊 /rating"],
        ["👤 /profile", "✏️ /editprofile"],
        ["📜 /rules", "🙈 /hide"]
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
        # имя уже было сохранено ранее, но обновим на всякий
        store_user(user)
        text = f"{display_user(user.id)} покинула чат, будем скучать💔"
        await context.bot.send_message(chat_id=cmu.chat.id, text=emo(text), parse_mode="HTML")

# ===================== /START и /ABOUT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(
        emo("Привет! Я — Мать Богинь для клана OnlyGirls💖\nНапиши /about чтобы узнать мои команды."),
        reply_markup=MAIN_KB
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(emo(
        "✨ Команды:\n"
        "/menu — открыть клавиатуру\n"
        "/editprofile — заполнить/обновить профиль (пошагово)\n"
        "/profile — показать твой профиль\n"
        "/pipisa — вырастить/уменьшить пипису (1 раз в день)\n"
        "/duel @юзер — дуэль пипис (до 3 в день)\n"
        "/top5 — топ-5 по пиписе\n"
        "/rating — полный рейтинг пипис\n"
        "/predskaz — предсказание дня (1 раз в день)\n"
        "/hugs [@юзер] — обнимашки (для всех/указанной)\n"
        "/lesbi — лесби-пара дня (1 раз в день)\n"
        "/role [@юзер] — «кто сегодня самая…»\n"
        "/rules — правила клана (ссылка)\n"
        "/hide — убрать клавиатуру"
    ))

# ===================== /RULES (ссылка) =====================
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(
        emo('Котик, правила клана <a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a>🫶'),
        parse_mode="HTML"
    )

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
    await update.message.reply_text(emo("Как тебя зовут?(имя)"))
    return STEP_NAME

async def step_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["name"] = update.effective_user.mention_html()
    await update.message.reply_text(emo("Какой у тебя ник в игре?"))
    return STEP_NICK

async def step_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["nickname"] = update.message.text.strip()
    await update.message.reply_text(emo("Какой у тебя UID?"))
    return STEP_UID

async def step_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["uid"] = update.message.text.strip()
    await update.message.reply_text(emo("Когда у тебя день рождения?(например, 01.01.2000 или 01.01)"))
    return STEP_BDAY

async def step_bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["bday"] = update.message.text.strip()
    await update.message.reply_text(emo("Из какого ты города?"))
    return STEP_CITY

async def step_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["city"] = update.message.text.strip()
    await update.message.reply_text(emo("Оставь ссылку на TikTok или просто свой ник(@username):"))
    return STEP_TIKTOK

async def step_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    context.user_data["profile_answers"]["tiktok"] = update.message.text.strip()
    await update.message.reply_text(emo("Поделись своим девизом или любимой цитатой:"))
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
    await update.message.reply_text(emo("Профиль обновлён✅"))
    return ConversationHandler.END

# ===================== ПИПИСА =====================
PIPISA_UP_REACTIONS = [
    "Она стремится к вершинам!📈",
    "Вперед и выше—гордимся!🥳",
    "Так растёт только легенда!🌟",
    "Сияет и радует хозяйку!✨",
]
PIPISA_DOWN_REACTIONS = [
    "Ничего, завтра вернём позиции💪",
    "Иногда и героям нужен отдых🌧️",
    "Обнимем—и всё пройдёт🫂",
    "Сменим вайб—пойдёт вверх🌈",
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
        await update.message.reply_text(emo("Пипису можно растить/мерить только раз в день!🌱"))
        return

    delta = _rand_delta()
    new_val = round(float(u.get("pipisa", 0.0)) + delta, 1)
    if new_val < -50.0:
        new_val = -50.0

    u["pipisa"] = new_val
    u["last_pipisa"] = today_str()
    save_state()

    if delta > 0:
        phrase = random.choice([
            f"🍆Твоя пиписа выросла на {delta:.1f} см!{random.choice(PIPISA_UP_REACTIONS)} Теперь: {new_val:.1f} см.",
            f"🍆Ого! +{delta:.1f} см—вот это рост!{random.choice(PIPISA_UP_REACTIONS)} Текущий размер: {new_val:.1f} см.",
        ])
    else:
        phrase = random.choice([
            f"🍆Оу… пиписа уменьшилась на {abs(delta):.1f} см.{random.choice(PIPISA_DOWN_REACTIONS)} Сейчас: {new_val:.1f} см.",
            f"🍆Немного просела({abs(delta):.1f} см).{random.choice(PIPISA_DOWN_REACTIONS)} Текущий размер: {new_val:.1f} см.",
        ])
    await update.message.reply_text(emo(phrase), parse_mode="HTML")

# ===================== ДУЭЛЬ (до 3/день) =====================
def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

async def duel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    me = update.effective_user
    ensure_user(me.id)
    state["users"][str(me.id)]["username"] = (me.username or "").lower()

    # цель: reply приоритетно, потом @username
    target_id = None
    if update.message and update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        arg = context.args[0].strip().lstrip("@")
        target_id = find_user_id_by_username(arg)

    if not target_id:
        await update.message.reply_text(emo("Отметь соперницу: /duel @username или ответь на её сообщение командой /duel."))
        return
    if target_id == me.id:
        await update.message.reply_text(emo("С собой дуэлиться нельзя🙃"))
        return

    ensure_user(target_id)
    me_u = state["users"][str(me.id)]
    tg_u = state["users"][str(target_id)]

    # лимит 3 в день
    if me_u.get("last_duel_date") != today_str():
        me_u["last_duel_date"] = today_str()
        me_u["duel_uses"] = 0
    if me_u["duel_uses"] >= 3:
        await update.message.reply_text(emo("Ты уже провела 3 дуэли сегодня. Попробуй завтра🌙"))
        return

    my_power = int(me_u.get("pipisa_power", 0))
    opp_power = int(tg_u.get("pipisa_power", 0))
    win_chance = 0.50 + 0.05 * (my_power - opp_power)
    win_chance = _clamp(win_chance, 0.20, 0.80)

    amount = round(random.uniform(0.1, 3.0), 1)
    win = (random.random() < win_chance)

    me_size = float(me_u.get("pipisa", 0.0))
    tg_size = float(tg_u.get("pipisa", 0.0))

    if win:
        steal = min(amount, tg_size + 50.0)  # у соперницы может быть минус—воруем до логики размера
        me_u["pipisa"] = round(me_size + steal, 1)
        tg_u["pipisa"] = round(tg_size - steal, 1)
        me_u["pipisa_power"] = me_u.get("pipisa_power", 0) + 2
        tg_u["pipisa_power"] = tg_u.get("pipisa_power", 0) + 1
        outcome = (
            f"⚔️ {me.mention_html()} победила в дуэли у {display_user(target_id)}!\n"
            f"🍆 Перешло {steal:.1f} см→теперь у тебя {me_u['pipisa']:.1f} см, у соперницы {tg_u['pipisa']:.1f} см."
        )
        tail = random.choice(["Легенда усилилась!💪", "Сила растёт—берегитесь!✨", "Очень опасная богиня…👑"])
    else:
        steal = min(amount, me_size + 50.0)
        me_u["pipisa"] = round(me_size - steal, 1)
        tg_u["pipisa"] = round(tg_size + steal, 1)
        me_u["pipisa_power"] = me_u.get("pipisa_power", 0) + 1
        tg_u["pipisa_power"] = tg_u.get("pipisa_power", 0) + 2
        outcome = (
            f"⚔️ {me.mention_html()} проиграла дуэль {display_user(target_id)}...\n"
            f"🍆 Ушло {steal:.1f} см→теперь у тебя {me_u['pipisa']:.1f} см, у соперницы {tg_u['pipisa']:.1f} см."
        )
        tail = random.choice(["Ничего, завтра реванш!🫶", "Обнимашки и вперёд к победам🤗", "Опыт тоже сила!🌟"])

    me_u["duel_uses"] += 1
    save_state()
    await update.message.reply_text(emo(outcome + "\n" + tail), parse_mode="HTML")

# ===================== РЕЙТИНГИ =====================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)[:5]
    if not rows:
        await update.message.reply_text(emo("Рейтинг пуст. Поливай пипису чаще🌱"))
        return
    text = "🏆 ТОП-5 пипис клана:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or tg_link_from_id(int(uid), uid)}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(emo(text), parse_mode="HTML")

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)
    if not rows:
        await update.message.reply_text(emo("Рейтинг пуст. Поливай пипису чаще🌱"))
        return
    text = "📊 Полный рейтинг пипис:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or tg_link_from_id(int(uid), uid)}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(emo(text), parse_mode="HTML")

# ===================== ПРЕДСКАЗАНИЯ (200) =====================
PREDICTIONS = [
    "Сегодня твой день—даже если облачно☁️",
    "Улыбка решит больше, чем кажется😊",
    "Делай по любви—и будет кайф💖",
    "Вселенная сегодня на твоей стороне✨",
    "Ты видишь больше, чем другие—доверься себе👁️",
    "Маленький шаг тоже движение вперёд👣",
    "Слухи остаются слухами—будь выше🕊️",
    "Пусть душа сегодня потанцует💃",
    "Ты—чьё-то «повезло»🍀",
    "Скажи себе «молодец»—ты это услышишь🥰",
    "Будь добрее к себе, ты стараешься💗",
    "Лёгкая магия рядом—просто вдохни🌬️",
    "Одна искренняя фраза изменит день✉️",
    "Твоя нежность—твоя сила🌸",
    "Смелость сегодня окупится🛡️",
    "Случайная встреча окажется важной🤝",
    "Дай миру то, что хочешь получить🌍",
    "Пусть будет уютно внутри🫶",
    "Там, где любовь—там и путь❤️",
    "Всему своё время—ты успеешь⏳",
    "Сегодня получится то, что не получалось вчера💫",
    "Вдохновляйся тем, что реально радует🌷",
    "Ты красивее, чем думаешь😌",
    "Легко—не значит пусто, просто легко🌿",
    "Всегда можно мягче—попробуй🧸",
    "Обернись: ты уже далеко прошла🛤️",
    "Небольшая победа—тоже победа🏅",
    "Тепло, которое ты даёшь, вернётся🔁",
    "Мир ждёт твою улыбку😁",
    "Ты—главный персонаж своей истории📖",
    "Доверяй интуиции—она громко шепчет🔮",
    "Сделай паузу и выпей воды💧",
    "Не сравнивай—сияй своим светом✨",
    "Сегодня можно чуть больше, чем вчера🚪",
    "Ты достойна именно того, чего хочешь💍",
    "Признай себе, что гордишься собой🪞",
    "Бери только то, что по любви🤍",
    "Смех сегодня лечит лучше всего😂",
    "Ты—девочка с космосом в глазах🌌",
    "Границы—это тоже любовь к себе🧭",
    "Позволь себе быть уязвимой—это красиво💞",
    "Путь станет яснее после первого шага🪜",
    "Ты умеешь больше, чем думаешь🧠",
    "Скажи «да» тому, что зовёт🚀",
    "Ты нравишься людям больше, чем предполагаешь🫶",
    "Спрячься в уют на 15 минут—это законно☕️",
    "Нежность сегодня победит грубость🌼",
    "Ты можешь всё, но не обязана всё сразу🧩",
    "Ваши мечты соглашаются на план✍️",
    "Искренность—твоя суперсила🦸‍♀️",
    "Не нужно спешить—всё по твоему таймингу⏱",
    "Тебя уже достаточно💗",
    "Сверкай, но по-своему✨",
    "Мир подстроится под твою любовь к себе💓",
    "Пусть будет чуть больше лёгкости🌈",
    "Вдохни глубже—и станет тише внутри🫁",
    "Ты—причина чьей-то веры в добро🌟",
    "Счастье в мелочах—найди три прямо сейчас🔎",
    "Сегодня тебя заметят—будь собой👀",
    "Не идеальность делает тебя идеальной💐",
    "Ты—та самая девочка-обнимашка🤗",
    "Грусть временная, а ты—навсегда💞",
    "Доверяй людям выборочно и себе безусловно🔐",
    "Ты—волшебница уютных вечеров🌙",
    "Не жди разрешения, просто живи💫",
    "Доброе утро начинается с доброй мысли🌅",
    "Пусть всё случится мягко и своевременно🫧",
    "Сделай что-то красивое для себя🫶",
    "Счастье любит твоё имя💌",
    "Лучшая версия тебя—уже здесь💎",
    "Ты—причина для танца💃",
    "У тебя получится. Точка✅",
    "Сегодня ты кому-то вдохновение✨",
    "Обмани тревогу объятием🫂",
    "Пусть сердце сегодня будет лёгким🪽",
    "То, что твоё—найдёт тебя🧭",
    "Ты умеешь делать тепло из ничего🔥",
    "Попроси о помощи—это тоже сила🤝",
    "Твоя нежность лечит людей рядом💗",
    "Ты—сияющая звёздочка⭐️",
    "Смени музыку—сменится настроение🎧",
    "Улыбайся—это идёт твоим глазам👁‍🗨",
    "Пусть будет день без самокритики🪷",
    "Ты любима больше, чем кажется💞",
    "Сделай шаг навстречу себе👣",
    "Дай себе минутку тишины🔕",
    "Вселенная слышит твой шёпот🌌",
    "Доброта—это твой бренд🛍",
    "Красота—это ты, когда спокойна🌊",
    "Сегодня лучшее слово—«нежно»🌸",
    "Ты—главный ресурс своей жизни⚡️",
    "Силы придут, когда перестанешь ругать себя💗",
    "Девочка, ты справляешься!🌟",
    "Любовь к себе—не эгоизм, а воздух💨",
    "Счастье—это мягкий плед и ты🧣",
    "Будь бережна к себе сегодня🧴",
    "Никто, кроме тебя, не решает, кто ты👑",
    "Ты достойна любви без условий💝",
    "Сегодня тебя ждёт маленькое чудо✨",
    "Пусть звонкий смех прозвучит хотя бы раз😂",
    "Ты—синоним слова «красиво»💘",
    "Твоё сердце знает маршрут🗺",
    "Смотри на себя глазами подруги—и улыбнись🥰",
    "Ты—именно та, кто нужна миру сейчас🌍",
    "Границы—это уют, а не стены🧱",
    "Становись собой, а не удобной🦋",
    "Не забывай: ты—подарок🎁",
    "Сомнения—просто облака, а ты—небо☁️",
    "Твои мечты законны📝",
    "Никто не сияет твоим светом—кроме тебя✨",
    "Помни: ты не обязана тащить всех🧺",
    "Выдохни ожидания—вдохни лёгкость🌿",
    "Ты—хорошая. Уже. Сейчас.🤍",
    # ещё 100
    "Сегодня удача улыбнётся в самом милом месте😊",
    "Ты сильнее вчерашних сомнений💪",
    "Выбирай мягкое—это работает🧸",
    "Твоя улыбка—лекарство для подруги рядом💗",
    "Внутри тебя—дом, где тебя любят🏡",
    "Сделай себе чаёк и полюби этот момент🍵",
    "Слова «я молодец» уже меняют день✨",
    "Будь той, кто утешает саму себя бережно🫂",
    "Сияй так, как умеешь именно ты✨",
    "Сегодня хороший день для тёплой смелости🌞",
    "Ты—чудо, которое забыло, что оно чудо🌟",
    "Мир не рушится, если ты отдыхаешь🛌",
    "Маленькие радости—большие спасатели🎈",
    "Пусть будет встреча, после которой легче🤍",
    "Ты—та, с кем хочется молчать в уюте🤫",
    "Скажи «нет» без чувства вины🚫",
    "Твоя красота—в живости, а не в шаблонах🌸",
    "Позволь себе не знать—и идти всё равно🧭",
    "Ты—девочка-сюрприз, и это прекрасно🎁",
    "Пусть будет совпадение, которое обнимает🔗",
    "Не сравнивай путь—сравнивай улыбки😌",
    "Ты—светлая мысль этого дня☀️",
    "Позвони той, кто любит тебя такой📞",
    "Время выбрать себя—всегда сейчас⏰",
    "Помни: ты—не «слишком», ты—«в самый раз»🫶",
    "Спрячься в плед и стань теплее миру🧣",
    "Ты—богиня маленьких шагов👣",
    "Пусть твой взгляд будет добр к себе🪞",
    "Твоё сердечко знает ритм счастья💓",
    "Стань себе лучшей подругой🤍",
    "Улыбнись в отражение—девочка из него ждёт😊",
    "Ты—улыбка вселенной сегодня🌌",
    "Дай себе быть несовершенной и любимой💗",
    "Пусть мир сегодня будет мягким🧶",
    "Ты заслуживаешь «просто так»🎀",
    "Пусть будет новость, которая согреет📰",
    "Ты—редкость, и это чувствуется💎",
    "Обнимай себя мысленно—это работает🫂",
    "Пусть тревоги схлопнутся от нежности🫧",
    "Спокойно—ты на своём пути🛤️",
    "Тебя невозможно повторить, и это сила🦋",
    "Сделай фоточку и полюби себя ещё раз📸",
    "Твоя энергия сегодня чарует✨",
    "Скажи «спасибо» себе за всё, что уже сделано🙏",
    "Ты—девочка-облако нежности☁️",
    "Внутри тебя уже есть ответы🔑",
    "Стань чуть добрее к себе, чем вчера💞",
    "Ты умеешь быть домом для себя🏠",
    "Пусть сердце шепчет, а ты слушаешь💌",
    "Сегодня ты будешь кому-то очень нужна🤍",
    "Ты—песня, которую хочется слушать🌸",
    "Вдохновение уже идёт к тебе навстречу🕊️",
    "Выбор себя—самый красивый выбор👑",
    "Твоя улыбка делает мир проще😊",
    "Сомнения—не истина, а варианты🤔",
    "Пусть будет один смелый шаг🚶‍♀️",
    "Ты прекрасна именно сейчас💐",
    "Поблагодари себя и расслабь плечики🧘‍♀️",
    "Сверкай по-своему, без объяснений✨",
    "Пусть утро пахнет надеждой🌅",
    "Сегодня тебя ждёт приятный сюрприз🎁",
    "Спроси себя: «чего хочется?»—и сделай🍰",
    "Ты—комплимент этому миру💖",
    "Пусть день будет с мягкими углами🧸",
    "Ты—девочка света, и это видно🌟",
    "Пусть ладошки станут теплее—от добра🤲",
    "Не обесценивай—ты правда молодец💗",
    "Замедлись—и мир станет добрее🕰",
    "Ты—настроение «уют»🧣",
    "Сегодня можно гордиться собой без «но»🏅",
    "Пусть найдётся причина искренне рассмеяться😂",
    "Ты—та, кого ищет вдохновение✨",
    "Дыши глубже—и станет легче🫁",
    "Твоя мягкость сильнее, чем кажется🌸",
    "Пусть всё получится красивым путём🎀",
    "Ты—сияние, которое не спрятать✨",
    "Обернись к себе с любовью—и всё сложится❤️",
    "Ты—прекрасная случайность мира🌍",
    "Сегодня сделай что-то только для себя💐",
    "Ты—девочка, которой точно можно доверять🤍",
    "Пусть ощущение дома будет рядом🏡",
    "Ты—лучшее, что с тобой случалось🌟",
    "Мир благодарит тебя за твою доброту🙏",
    "Ты умеешь беречь—и тебя берегут🫶",
    "Повернись к солнцу и согрейся☀️",
    "У тебя есть право не спешить🐢",
    "Сегодня твой свет увидят те, кому нужно🔦",
    "Ты—девочка-красота, и точка💗",
    "Заслуживаешь всего, что просишь у жизни🌈",
    "Твоя душа—как сад, поливай любовью🌷",
    "Ты—маленькая вселенная чудес🌌",
    "Пусть всё складывается как пазл🧩",
    "Ты делаешь мир безопаснее своей нежностью🕊️",
    "Обними себя прямо сейчас—я разрешаю🤗",
    "Ты—из тех, кого хочется беречь💖",
    "Смейся смелее—это красиво😂",
    "Пусть будет солнечный луч внутри☀️",
    "Ты—ответ на чью-то просьбу о добре🤍",
    "Просто будь—и этого достаточно🪷",
    "Лёгкая радость уже бежит к тебе🐾",
    "Ты—причина появиться надежде🌟",
    "Сделай шаг навстречу новой себе🚪",
    "Пусть сердце будет спокойным и тёплым🔥",
    "Ты—вдох, которым дышит доброта🌬️",
    "Сегодня мир подмигнет тебе😉",
    "Ты прекрасная, честно-честно💗",
]

async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]
    u["username"] = (update.effective_user.username or "").lower()
    if u.get("last_prediction") == today_str():
        await update.message.reply_text(emo("🔮 Предсказание уже было сегодня!"))
        return
    u["last_prediction"] = today_str()
    save_state()
    await update.message.reply_text(emo(f"🔮 {random.choice(PREDICTIONS)}"))

# ===================== HUGS =====================
HUGS_POOL = [
    "🤗 {a} крепко обняла {b}—тепло доставлено по адресу🧸",
    "💞 {a} нежно прижалась к {b}—пусть тревоги тают🌷",
    "🥰 {a} согрела {b} своими обнимашками—зарядилась любовью!",
    "🫶 {a} и {b}—сегодня самый милый дуэт!",
    "Кто не обнимется—тот не играет в кастомке!",
    "🫂 Токсиков тоже иногда обнимают… по голове… табуреткой🙃",
    "Передаю мягкость, заботу и печеньку🍪 — {a}→{b}",
    "Крепко-крепко и очень нежно—трепещи, грусть!🫂 {a} обняла {b}",
    "Пусть тревоги уменьшаются на 50% после этих объятий🌸 {a} для {b}",
]

async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    me = update.effective_user

    # если указали @юзер — попробуем найти ID
    if context.args:
        raw = context.args[0]
        uid = find_user_id_by_username(raw)
        if uid:
            a = me.mention_html()
            b = display_user(uid)
            tpl = random.choice(HUGS_POOL)
            text = tpl.format(a=a, b=b) if ("{a}" in tpl or "{b}" in tpl) else f"{a} обняла {b}—{tpl}"
            await update.message.reply_text(emo(text), parse_mode="HTML")
        else:
            # как ввели
            msg = random.choice([
                f"🤗 {me.mention_html()} обняла {raw}!Тепло доставлено🧸",
                f"💞 {me.mention_html()} отправила объятия {raw}.Всё будет хорошо🌷",
            ])
            await update.message.reply_text(emo(msg), parse_mode="HTML")
        return

    # иначе—рандом из известных
    pool = [uid for uid in state.get("known_users", []) if uid != me.id]
    if not pool:
        await update.message.reply_text(emo("Обнимашки для всех в чате!🫂"))
        return
    target_id = random.choice(pool)
    a = me.mention_html()
    b = display_user(target_id)
    tpl = random.choice(HUGS_POOL)
    text = tpl.format(a=a, b=b) if ("{a}" in tpl or "{b}" in tpl) else f"{a} обняла {b}—{tpl}"
    await update.message.reply_text(emo(text), parse_mode="HTML")

# ===================== ЛЕСБИ-ПАРА =====================
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    pool = list(set(state.get("known_users", [])))
    if len(pool) < 2:
        await update.message.reply_text(emo("Недостаточно участниц для пары"))
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
        "🫶 Кто бы мог подумать! {a} и {b}—пара дня!",
        "💘 Амур попал точно в цель! {a} и {b} теперь вместе😍",
        "💞 Любовь витает в воздухе: {a} + {b} =❤️",
    ]
    msg = random.choice(lines).format(a=display_user(a), b=display_user(b))
    await context.bot.send_message(chat_id=CHAT_ID, text=emo(msg), parse_mode="HTML")

# ===================== РОЛИ /role =====================
ROLES = [
    "самая красивая девочка💖","самая милая киска😺","самая нежная принцесса🌸","самая грустная пельмешка😔",
    "самая сияющая звёздочка✨","самая злая ведьмочка🧙‍♀️","самая модная иконка👠","самая загадочная душа🌀",
    "самая радужная булочка🌈","самая одинокая тучка🌧","какашка дня💩","бунтарка чата🔥","психованная фея🤯",
    "плакса дня😭","драмаквин вечера👑","самая громкая жаба🐸","киска с характером🐾","королева спама📱",
    "самая непредсказуемая🎲","девочка вайба🎧","самая эстетичная на районе🎨","инста-дива дня📸",
    "самая поющая в душе🎤","самая секси в пижаме💃","королева вечеринки🎉","девочка с космосом в глазах🌌",
    "богиня флирта💋","дева хаоса🫦","секретный агент чата🕵️‍♀️","персик дня🍑","кошмар всех бывших💔",
    "кофейная богиня☕️","самая громкая ржунька😂","девочка-сюрприз🎲","случайный гений🧠",
    "ловушка для сердец❤️‍🔥","обнимашка на ножках🤗","самая ранимая душа🥺","носик-кнопочка дня👃",
    "девочка, которой хочется чай налить🍵","сердце на распашку💘","сладость с начинкой из грусти🍬",
    "облако нежности☁️","милашка дня🧸","тёплый плед среди шторма🫂","улыбка, за которую прощаешь всё😊",
    "девочка-обнимашка🤍","самая драматичная🎭","капризуля дня😈","девочка с планом(и бартером)📋",
    "высшая лига феминизма🧜‍♀️","та, кто делает мозги🥴","шальная императрица👑","главная звезда чата🌟",
    "самая занятная интриганка🧩","девочка с короной по умолчанию👸","фея с бдсм-крыльями🧚‍♀️",
    "заколдованная котлетка🍖","волшебница уютных вечеров🌙","мистическая богиня сна😴","ведьма на минималках🧙‍♀️",
    "ведьма, которая не варит борщ🧹","девочка-зелье🧪","та, что танцует под луной💃","девочка-ой-всё🙄",
    "пиписка на каблуках🍆","грустный котик в теле стервы😿","та, что не отвечает🙅‍♀️","кринж-королева🫠",
    "шарик тревожности🎈","хитрая жопка🍑","пустое место💨","позор клана🤡","ошибка природы⚠️","фиаско дня📉",
    "ходячий кринж🫠","минус в карму👎","неудача недели💀","хз кто и зачем тут🙃","причина стыда сегодня😬",
    "баг в матрице🕳","главный повод для фейспалма🤦‍♀️","самая бесячая🧿","фейл века😵","анти-звезда чата🚫",
    "проклятие дня🧟‍♀️","катастрофа в юбке🌪","повод выйти из чата🚪","фоновый шум🔇","глюк системы🖥",
    "недоразумение с вайбом😵‍💫","рандомная npc💻","баг с лицом🫥","урон по глазам👁","та, кого лучше не вспоминать👻",
    "моральный вирус🦠","сомнительная личность🕳","бан без суда и следствия🚷"
]

async def role_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    # приоритет: reply → @username → random
    if update.message and update.message.reply_to_message:
        target = update.message.reply_to_message.from_user
        store_user(target)
        target_html = target.mention_html()
    elif context.args:
        raw = context.args[0].strip()
        uid = find_user_id_by_username(raw)
        if uid:
            target_html = display_user(uid)
        else:
            # если не нашли — покажем как написали
            target_html = raw if raw.startswith("@") else f"@{raw}"
    else:
        pool = [uid for uid in set(state.get("known_users", [])) if uid != update.effective_user.id]
        if not pool:
            await update.message.reply_text(emo("Нужно хотя бы две участницы в базе✨ Скажи девочкам написать что-нибудь в чат."))
            return
        rnd_id = random.choice(pool)
        target_html = display_user(rnd_id)

    role_text = random.choice(ROLES)
    await update.message.reply_text(emo(f"{target_html} сегодня {role_text}"), parse_mode="HTML")

# ===================== ДЕНЬ РОЖДЕНИЯ (ежедневная проверка) =====================
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
            text = f"🎂 Сегодня день рождения у {name}!Пожелаем счастья, любви и побед!🥳"
            try:
                await context.bot.send_message(chat_id=CHAT_ID, text=emo(text), parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Не удалось отправить поздравление: {e}")

# ===================== РЕГИСТРАЦИЯ И ЗАПУСК =====================
def build_application():
    app = ApplicationBuilder().token(TOKEN).build()

    # Приветствия/прощания
    app.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(farewell_member, ChatMemberHandler.CHAT_MEMBER))

    # Профиль (пошагово)
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
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("hide", hide))

    # Фан/игры
    app.add_handler(CommandHandler("pipisa", pipisa))
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("hugs", hugs))
    app.add_handler(CommandHandler("lesbi", lesbi))
    app.add_handler(CommandHandler("role", role_cmd))

    # Предсказание
    app.add_handler(CommandHandler("predskaz", predskaz))

    # JobQueue — поздравления с ДР (каждый день в 09:00 по серверу)
    app.job_queue.run_daily(birthday_job, time(hour=9, minute=0))

    return app

if __name__ == "__main__":
    application = build_application()
    print("OnlyGirls bot запущен…")
    application.run_polling(close_loop=False)
