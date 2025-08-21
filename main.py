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
            for suid, u in state.get("users", {}).items():
                if "username" not in u:
                    u["username"] = ""
                if "pipisa_power" not in u:
                    u["pipisa_power"] = 0
                if "last_duel_date" not in u:
                    u["last_duel_date"] = None
                if "duel_uses" not in u:
                    u["duel_uses"] = 0
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

# убираем пробелы перед эмодзи в исходящем тексте
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

# ===================== /START и /ABOUT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(
        emo("Привет! Я — Мать Богинь для клана OnlyGirls💖 Напиши /about чтобы узнать мои команды."),
        reply_markup=MAIN_KB
    )

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(emo(
        "✨ Команды:\n/menu — открыть клавиатуру\n/editprofile — заполнить/обновить профиль(пошагово)\n/profile — показать твой профиль\n/pipisa — вырастить/уменьшить пипису(1 раз в день, минимум −50 см)\n/duel @юзер — дуэль пипис(до 3 в день, сила растёт)\n/top5 — топ-5 по пиписе\n/rating — полный рейтинг пипис\n/predskaz — предсказание дня(1 раз в день)\n/hugs [@юзер] — обнимашки(для всех/указанной)\n/lesbi — лесби-пара дня(1 раз в день)\n/role [@юзер] — «кто сегодня самая…»\n/rules — правила клана(ссылка)\n/info — актуальная инфа(ссылка)\n/hide — убрать клавиатуру"
    ))

# ===================== /RULES (ссылка) =====================
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    await update.message.reply_text(
        emo('Котик, правила клана <a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a>🫶'),
        parse_mode="HTML"
    )

# ===================== /INFO (ссылка «Здесь…») =====================
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
    "Она стремится к вершинам!📈","Вперед и выше—гордимся!🥳","Так растёт только легенда!🌟","Сияет и радует хозяйку!✨"
]
PIPISA_DOWN_REACTIONS = [
    "Ничего, завтра вернём позиции💪","Иногда и героям нужен отдых🌧️","Обнимем—и всё пройдёт🫂","Сменим вайб—пойдёт вверх🌈"
]

def _rand_delta():
    d = round(random.uniform(-10.0, 10.0), 1)
    if abs(d) < 0.1:
        d = 0.1 if random.random() > 0.5 else -0.1
    return d

def _clamp(v, lo, hi):
    return max(lo, min(hi, v))

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
    new_val = max(new_val, -50.0)
    u["pipisa"] = new_val
    u["last_pipisa"] = today_str()
    save_state()
    if delta > 0:
        phrase = random.choice([
            f"🍆Твоя пиписа выросла на {delta:.1f} см!{random.choice(PIPISA_UP_REACTIONS)} Теперь: {new_val:.1f} см.",
            f"🍆Ого! +{delta:.1f} см—вот это рост!{random.choice(PIPISA_UP_REACTIONS)} Текущий размер: {new_val:.1f} см."
        ])
    else:
        phrase = random.choice([
            f"🍆Оу… пиписа уменьшилась на {abs(delta):.1f} см.{random.choice(PIPISA_DOWN_REACTIONS)} Сейчас: {new_val:.1f} см.",
            f"🍆Немного просела({abs(delta):.1f} см).{random.choice(PIPISA_DOWN_REACTIONS)} Текущий размер: {new_val:.1f} см."
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
        await update.message.reply_text(emo("Отметь соперницу: /duel @username или ответь на её сообщение командой /duel."))
        return
    if target_id == me.id:
        await update.message.reply_text(emo("С собой дуэлиться нельзя🙃"))
        return
    ensure_user(target_id)
    me_u = state["users"][str(me.id)]
    tg_u = state["users"][str(target_id)]
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
        steal = min(amount, tg_size + 50.0)
        me_u["pipisa"] = round(me_size + steal, 1)
        tg_u["pipisa"] = round(tg_size - steal, 1)
        me_u["pipisa_power"] = me_u.get("pipisa_power", 0) + 2
        tg_u["pipisa_power"] = tg_u.get("pipisa_power", 0) + 1
        me_u["pipisa"] = max(me_u["pipisa"], -50.0)
        tg_u["pipisa"] = max(tg_u["pipisa"], -50.0)
        outcome = (
            f"⚔️ {me.mention_html()} победила в дуэли у {display_user(target_id)}!"
            f"\n🍆 Перешло {steal:.1f} см→теперь у тебя {me_u['pipisa']:.1f} см, у соперницы {tg_u['pipisa']:.1f} см."
        )
        tail = random.choice(["Легенда усилилась!💪","Сила растёт—берегитесь!✨","Очень опасная богиня…👑"])
    else:
        steal = min(amount, me_size + 50.0)
        me_u["pipisa"] = round(me_size - steal, 1)
        tg_u["pipisa"] = round(tg_size + steal, 1)
        me_u["pipisa_power"] = me_u.get("pipisa_power", 0) + 1
        tg_u["pipisa_power"] = tg_u.get("pipisa_power", 0) + 2
        me_u["pipisa"] = max(me_u["pipisa"], -50.0)
        tg_u["pipisa"] = max(tg_u["pipisa"], -50.0)
        outcome = (
            f"⚔️ {me.mention_html()} проиграла дуэль {display_user(target_id)}..."
            f"\n🍆 Ушло {steal:.1f} см→теперь у тебя {me_u['pipisa']:.1f} см, у соперницы {tg_u['pipisa']:.1f} см."
        )
        tail = random.choice(["Ничего, завтра реванш!🫶","Обнимашки и вперёд к победам🤗","Опыт тоже сила!🌟"])
    me_u["duel_uses"] += 1
    save_state()
    await update.message.reply_text(emo(outcome + " " + tail), parse_mode="HTML")

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

# ===================== 200 ПРЕДСКАЗАНИЙ =====================
PREDICTIONS = [
    "Сегодня твой день—даже если облачно☁️","Улыбка решит больше, чем кажется😊","Делай по любви—и будет кайф💖","Вселенная сегодня на твоей стороне✨","Ты видишь больше, чем другие—доверься себе👁️","Маленький шаг тоже движение вперёд👣","Слухи остаются слухами—будь выше🕊️","Пусть душа сегодня потанцует💃","Ты—чьё-то «повезло»🍀","Скажи себе «молодец»—ты это услышишь🥰",
    "Спокойствие—твоя суперсила сегодня🧘‍♀️","Выбери доброту—это заметят🌷","Новость дня будет приятной📨","Пей воду и сияй как бриллиант💎","Случайный комплимент изменит настроение🌈","Твоя интуиция права—доверься ей🔮","Сегодня лучше не спешить—ритм найдётся сам🎵","Поймай луч солнца и улыбнись☀️","Надень любимое—мир подыграет тебе👗","Кто-то тайно тобой восхищается👀",
    "Скажи «нет» лишнему—почувствуешь свободу🕊️","Скажи «да» себе—почувствуешь силу⚡️","Найди красивое в мелочах—в этом магия✨","Сделай паузу—вдох-выдох и дальше🌬️","Хорошая мысль найдёт тебя за чаем🍵","Ты важна для людей больше, чем думаешь💞","Сегодня легко получится то, что откладывала✅","Сделай фото—поймаешь момент дня📸","Вспомни мечту и приблизь её на 1 шаг🚶‍♀️","Слова доброты вернутся тебе эхом📡",
    "Убирайся под музыку—и мысли тоже разложатся🧹","Сегодня день лёгких совпадений🔗","Ты слышишь себя громче, чем шум вокруг🔊","Полюби свой темп—он правильный⌛️","Интернет подкинет полезную идею💡","Дай место чуду—оно любит простор🌌","Твоя энергия исцеляет других🌿","Сделай приятность без повода—вернётся сторицей🎁","Ничего не сломано—всё в процессе🛠","Твои дела под контролем—даже если не кажется🧭",
    "День удачных диалогов—говори честно💬","Улыбнись зеркалу—оно союзник🪞","Доверяй тихим чувствам—они точны🎯","Кофе сегодня особенно волшебный☕️","Не сравнивай—у тебя своя траектория🚀","Музыка дня найдёт тебя сама🎧","Слова благодарности откроют дверь🚪","Мягкость—не слабость, а сила🤍","Не трать энергию на ненужные споры🙅‍♀️","Тебя ждёт маленькая радость в пути🛤",
    "Заметишь знак—он для тебя🪄","Твоя доброта кому-то сегодня очень нужна🤝","Случайная встреча согреет сердце🔥","Запусти мини-ритуал заботы о себе🛁","Сон подскажет ответ сегодня ночью🌙","Ты достаточно—прямо сейчас💫","Не бойся попросить помощи—это мудро🧠","Сделай шаг в неизвестность—там интересно🗺","Сегодня легче, чем ты думаешь🎈","Твоя улыбка сегодня кому-то спасёт день🛟",
    "Ты светишься изнутри—заметно всем⭐️","Смени обои на телефоне—вместе сменится вайб📱","Разгрузи сумку и голову—станет легче🎒","Любимое блюдо подарит силы🍲","Самая красивая мысль придёт в дороге🚌","Ты умеешь больше, чем признаёшься себе🏅","Список дел сократится сам—доверяй потоку🌊","Отложи тяжёлое до завтра—сегодня ласка🌸","Спрячься в плед—мир подождёт🫶","Скажи «спасибо» себе—это важно🎀",
    "Сегодня слова ложатся мягко—используй их мудро📝","Твоё сердце знает дорогу домой🏡","Чудо уже выехало—останется только открыть дверь🚪","День для маленьких побед—собери коллекцию🏆","Ты магнит для хороших новостей📩","Мир не против тебя—он за тебя🤍","Ждать не страшно, страшно не мечтать🌠","Смелая мысль найдёт тебя первой🗯","Твоя внутренняя девочка хочет печеньку🍪","Ты причина чьей-то надежды сегодня🌟",
    "Красота начинается с принятия себя😍","Твоё лицо любит воду и сон—побалуй его💧","Твои глаза сияют даже без хайлайтера✨","Твоя улыбка—лучший аксессуар💋","Твоя кожа любит нежность—будь мягче с собой🫧","Красота—это твоё настроение, а не макияж🎨","Ты красива, когда веришь себе💖","Самое красивое в тебе—живость и огонь🔥","Тебе идёт смелость и честность💫","Твоя походка—как музыка, не останавливайся🎶",
    "Пусть волосы сегодня танцуют—и ты вместе с ними💃","Губы помнят комплименты—скажи их себе💌","Зеркало сегодня твой фан-клуб📣","Ты шедевр в любой одежде🖼","Твоему стилю достаточно твоего вкуса👗","Нежность—твой естественный хайлайтер🌟","Ты не обязана быть идеальной, чтобы быть прекрасной🌷","Каждая твоя черта—история, а не недостаток📚","Улыбнись глазами—мир растает🧊","Твои руки создают тепло—и это видно🤲",
    "Красота—это как ты заботишься о себе🫶","Лучи комплиментов летят к тебе—не уворачивайся💫","Ты фотогенична, потому что настоящая📸","Твой смех лечит морщины времени😂","Внутренняя богиня просит блеска—дай ей💎","Красота—это комфорт в своей коже🧴","Ты излучаешь стиль даже в пижаме💃","Сегодня ты вдохновение для чужого образа🎀","Твоя естественность роскошна без фильтров📲","Видно, как ты любишь себя—так держать❤️",
    "Ты можешь всё, но не всё сразу—выбери важное🎯","Сомнение тихо, но ты громче—действуй🔊","Страх—не знак «стоп», а знак «готовься»⚠️","План на 10 минут лучше, чем идеал на потом🧭","Начни с малого—и станет много📈","Не сравнивай старт с чужой финишной лентой🏁","Ты становишься тем, что повторяешь—выбирай мудро🔁","Отдых—часть стратегии, а не слабость🛌","Совершенство—ловушка, прогресс—свобода🧩","Побеждай любопытством, не насилием над собой🔍",
    "Если устала—иди медленно, но иди🐢","Сделай сегодня, за что завтра скажешь «спасибо»🙏","Спроси себя «а если получится?»—и попробуй🚀","Ты — проект всей жизни, наслаждайся процессом🛠","Не жди мотивации—начни и она подтянется🏗","Выбери одну важную задачу и доведи её до конца✅","Идеи приходят тем, кто работает с тем, что есть🧠","Ошибка—это опыт, а не приговор📘","Ты можешь менять правила своей игры🎮","Дисциплина это забота о будущей тебе🎁",
    "Учись радоваться маленьким результатам—они растят большие🌱","Скажи «да» новому навыку сегодня🧰","Твоя сила в том, что ты не сдаёшься💪","Каждый день—новый шанс для старой мечты🌅","Начни с двух минут—иногда этого достаточно⌚️","Сделай важное раньше, чем шумное🔕","То, что сложно—часто и ценно💎","Ты справлялась раньше—справишься и сейчас🛡","Не забывай хвалить себя по пути🏵","Сделай доброе дело и не рассказывай—магия усилится🪄",
    "Случайный смех—лучшее топливо для дня😄","Небо сегодня красивее обычного—заметь☁️","Ты встретишь знак, похожий на совпадение🔗","Слова любви к себе звучат убедительнее вслух💬","Подари кому-то 5 минут внимания—это много⏱","Доверяй людям, которые становятся теплее рядом с тобой🔥","Будь бережной к своим границам—это мудрость🚪","Выключи лишнее—станет слышно важное🔇","Тихая уверенность красивее громких обещаний🤍","Ты справляешься лучше, чем думаешь🌟",
    "Твоя доброта — не слабость, а выбор🌿","Иногда забота—это просто поесть вовремя🍽","День улыбнётся в ответ, если начнёшь первой🙂","Лёгкая прогулка решит тяжёлую мысль🚶‍♀️","Найди лучик смешного—и день станет легче😌","Твоя внимательность к себе заразительна для других🌼","Подумай, чего хочешь ты—и сделай это приоритетом📌","Радость не обязана быть громкой—пусть будет твоей🎁","Найди повод поблагодарить три раза сегодня3️⃣","Ты важнее своего списка дел🗒",
    "Помни: отдых тоже продуктивен🧘‍♀️","Выбирай, за что благодарна прямо сейчас💗","Твоя искренность создаёт пространство безопасности🛖","Пусть будет больше «можно», меньше «надо»🫶","Ты звучишь красивее, когда веришь себе🎙","Твоё присутствие—подарок для близких🎀","Стань на свою сторону—и мир подтянется🤝","Счастье любит простоту—не усложняй🍃","Сделай что-то только для себя—ты это заслужила💝","Сохраняй тепло—вдруг кому-то именно оно нужно🔥",
    "Ты — лучшая версия себя на сегодня🌸","Искра вдохновения уже рядом—будь внимательной✨","Поделись улыбкой—она умножается➕","Мир отвечает тем же тоном—выбирай мягкость🤍","Любовь к себе—это действие, не просто слова💌","Твоя храбрость красива даже в тишине🦁","Сегодня получится то, что не получалось вчера🔁","Ты — компас для себя, а не для всех🧭","Будь бережна к чувствам—и они ответят ясностью💧","Ты на верном пути—шаг за шагом👣"
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
    "🤗 {a} крепко обняла {b}—тепло доставлено по адресу🧸","💞 {a} нежно прижалась к {b}—пусть тревоги тают🌷","🥰 {a} согрела {b} своими обнимашками—зарядилась любовью!","🫶 {a} и {b}—сегодня самый милый дуэт!","Кто не обнимется—тот не играет в кастомке!","🫂 Токсиков тоже иногда обнимают… по голове… табуреткой🙃","Передаю мягкость, заботу и печеньку🍪 — {a}→{b}","Крепко-крепко и очень нежно—трепещи, грусть!🫂 {a} обняла {b}","Пусть тревоги уменьшаются на 50% после этих объятий🌸 {a} для {b}"
]

async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
    me = update.effective_user
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
            msg = random.choice([
                f"🤗 {me.mention_html()} обняла {raw}!Тепло доставлено🧸",
                f"💞 {me.mention_html()} отправила объятия {raw}.Всё будет хорошо🌷"
            ])
            await update.message.reply_text(emo(msg), parse_mode="HTML")
        return
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
        await update.message.reply_text(emo(f"👭 Пара дня уже выбрана: {display_user(a)} + {display_user(b)}💞"), parse_mode="HTML")
        return
    a, b = random.sample(pool, 2)
    state["last_lesbi_date"] = today_str()
    state["last_lesbi_pair"] = [a, b]
    save_state()
    lines = [
        "🌈 Сегодняшняя лесби-пара: {a} и {b}💋","🫶 Кто бы мог подумать! {a} и {b}—пара дня!","💘 Амур попал точно в цель! {a} и {b} теперь вместе😍","💞 Любовь витает в воздухе: {a} + {b} =❤️"
    ]
    msg = random.choice(lines).format(a=display_user(a), b=display_user(b))
    await context.bot.send_message(chat_id=CHAT_ID, text=emo(msg), parse_mode="HTML")

# ===================== РОЛИ /role =====================
ROLES = [
    "самая красивая девочка💖","самая милая киска😺","самая нежная принцесса🌸","самая грустная пельмешка😔","самая сияющая звёздочка✨","самая злая ведьмочка🧙‍♀️","самая модная иконка👠","самая загадочная душа🌀","самая радужная булочка🌈","самая одинокая тучка🌧","какашка дня💩","бунтарка чата🔥","психованная фея🤯","плакса дня😭","драмаквин вечера👑","самая громкая жаба🐸","киска с характером🐾","королева спама📱","самая непредсказуемая🎲","девочка вайба🎧","самая эстетичная на районе🎨","инста-дива дня📸","самая поющая в душе🎤","самая секси в пижаме💃","королева вечеринки🎉","девочка с космосом в глазах🌌","богиня флирта💋","дева хаоса🫦","секретный агент чата🕵️‍♀️","персик дня🍑","кошмар всех бывших💔","кофейная богиня☕️","самая громкая ржунька😂","девочка-сюрприз🎲","случайный гений🧠","ловушка для сердец❤️‍🔥","обнимашка на ножках🤗","самая ранимая душа🥺","носик-кнопочка дня👃","девочка, которой хочется чай налить🍵","сердце на распашку💘","сладость с начинкой из грусти🍬","облако нежности☁️","милашка дня🧸","тёплый плед среди шторма🫂","улыбка, за которую прощаешь всё😊","девочка-обнимашка🤍","самая драматичная🎭","капризуля дня😈","девочка с планом(и бартером)📋","высшая лига феминизма🧜‍♀️","та, кто делает мозги🥴","шальная императрица👑","главная звезда чата🌟","самая занятная интриганка🧩","девочка с короной по умолчанию👸","фея с бдсм-крыльями🧚‍♀️","заколдованная котлетка🍖","волшебница уютных вечеров🌙","мистическая богиня сна😴","ведьма на минималках🧙‍♀️","ведьма, которая не варит борщ🧹","девочка-зелье🧪","та, что танцует под луной💃","девочка-ой-всё🙄","пиписка на каблуках🍆","грустный котик в теле стервы😿","та, что не отвечает🙅‍♀️","кринж-королева🫠","шарик тревожности🎈","хитрая жопка🍑","пустое место💨","позор клана🤡","ошибка природы⚠️","фиаско дня📉","ходячий кринж🫠","минус в карму👎","неудача недели💀","хз кто и зачем тут🙃","причина стыда сегодня😬","баг в матрице🕳","главный повод для фейспалма🤦‍♀️","самая бесячая🧿","фейл века😵","анти-звезда чата🚫","проклятие дня🧟‍♀️","катастрофа в юбке🌪","повод выйти из чата🚪","фоновый шум🔇","глюк системы🖥","недоразумение с вайбом😵‍💫","рандомная npc💻","баг с лицом🫥","урон по глазам👁","та, кого лучше не вспоминать👻","моральный вирус🦠","сомнительная личность🕳","бан без суда и следствия🚷"
]

async def role_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    store_user(update.effective_user)
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
    app.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(ChatMemberHandler(farewell_member, ChatMemberHandler.CHAT_MEMBER))
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
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("rules", rules))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("hide", hide))
    app.add_handler(CommandHandler("pipisa", pipisa))
    app.add_handler(CommandHandler("duel", duel_cmd))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("hugs", hugs))
    app.add_handler(CommandHandler("lesbi", lesbi))
    app.add_handler(CommandHandler("role", role_cmd))
    app.job_queue.run_daily(birthday_job, time(hour=9, minute=0))
    return app

if __name__ == "__main__":
    application = build_application()
    print("OnlyGirls bot запущен…")
    application.run_polling(close_loop=False)
