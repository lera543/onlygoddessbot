# -*- coding: utf-8 -*-
import json
import logging
import random
from datetime import datetime, date, time
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ChatMemberHandler,
    ConversationHandler, ContextTypes, filters
)

# ===================== НАСТРОЙКИ =====================
TOKEN = "8215387975:AAHS_mMHzXBGtDVevEBiSwsLcLPChs7Yq7k"
CHAT_ID = -1001849339863
DATA_FILE = Path("data.json")

INFO_URL = "https://telegra.ph/Aktualnaya-informaciya-08-21"
RULES_URL = "https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29"

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO
)
logger = logging.getLogger("OnlyGirlsBot")

# ===================== ХРАНИЛИЩЕ =====================
# users: {
#   user_id(str): {
#     "name"(mention_html), "username"(str),
#     "nickname","uid","bday","city","tiktok","quote",
#     "pipisa"(float), "pipisa_power"(int), "last_pipisa"(YYYY-MM-DD),
#     "last_prediction"(YYYY-MM-DD),
#     "duel_used_on"(YYYY-MM-DD), "duel_uses"(int)
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

def today_str() -> str:
    return date.today().isoformat()

def ensure_user(user_id: int, username: str = None, mention_html: str = None):
    suid = str(user_id)
    if suid not in state["users"]:
        state["users"][suid] = {
            "name": mention_html or "",
            "username": username or "",
            "nickname": "",
            "uid": "",
            "bday": "",
            "city": "",
            "tiktok": "",
            "quote": "",
            "pipisa": 0.0,
            "pipisa_power": 0,
            "last_pipisa": None,
            "last_prediction": None,
            "duel_used_on": None,
            "duel_uses": 0
        }
    else:
        if mention_html and not state["users"][suid].get("name"):
            state["users"][suid]["name"] = mention_html
        if username and not state["users"][suid].get("username"):
            state["users"][suid]["username"] = username
    if user_id not in state.get("known_users", []):
        state["known_users"].append(user_id)

def mention_from_id(user_id: int, fallback_text: str = "девочка") -> str:
    suid = str(user_id)
    u = state["users"].get(suid)
    if u and u.get("name"):
        return u["name"]
    return f'<a href="tg://user?id={user_id}">{fallback_text}</a>'

def display_user(user_id: int) -> str:
    suid = str(user_id)
    u = state["users"].get(suid)
    if u and u.get("name"):
        return u["name"]
    if u and u.get("username"):
        return f'<a href="tg://user?id={user_id}">@{u["username"]}</a>'
    return f'<a href="tg://user?id={user_id}">девочка</a>'

def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")

# ===================== ТРЕКЕР ЛЮБЫХ СООБЩЕНИЙ =====================
async def track_seen_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not user:
        return
    ensure_user(user.id, user.username, user.mention_html())
    save_state()

# ===================== ПРИВЕТСТВИЕ / ПРОЩАНИЕ =====================
async def greet_or_bye(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    old = cmu.old_chat_member.status
    new = cmu.new_chat_member.status
    user = cmu.new_chat_member.user
    ensure_user(user.id, user.username, user.mention_html())
    if (old in ("left", "kicked")) and (new in ("member", "administrator", "creator")):
        text = f"Добро пожаловать, {user.mention_html()}❣️ Ознакомься пожалуйста с правилами клана (<a href=\"{RULES_URL}\">здесь</a>)🫶 Важная информация всегда в закрепе❗️ Клановая приставка: ঔ"
        await context.bot.send_message(chat_id=cmu.chat.id, text=text, parse_mode="HTML")
    elif (old in ("member", "administrator", "creator")) and (new in ("left", "kicked")):
        await context.bot.send_message(chat_id=cmu.chat.id, text=f"Пока-пока, {user.mention_html()}💗 Возвращайся скорее!", parse_mode="HTML")
    save_state()

# ===================== /START /ABOUT /INFO /RULES =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.mention_html())
    save_state()
    await update.message.reply_text("Привет! Я — Мать Богинь для клана OnlyGirls💖 Напиши /about чтобы увидеть команды.")

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✨ Команды: /editprofile — заполнить/обновить профиль (пошагово); /profile — показать твой профиль; /pipisa — вырастить/уменьшить пипису (1 раз в день); /duel [@юзер или reply] — пиписовая дуэль (до 3 раз/день); /top5 — топ-5 по пиписе; /rating — полный рейтинг пипис; /predskaz — предсказание дня (1 раз в день); /compliment [@юзер] — комплимент; /hugs [@юзер] — обнимашки; /lesbi — случайная парочка дня; /role [@юзер] — кто сегодня самая…; /info — актуальная информация; /rules — правила клана.")

async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Актуальную информацию по клану, кастомкам и т.д смотри <a href="{INFO_URL}">здесь🖤</a>', parse_mode="HTML")

async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f'Котик, правила клана <a href="{RULES_URL}">здесь</a>🫶', parse_mode="HTML")

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
            tt_line = f'📲TikTok: <a href="{tiktok}">TikTok</a>'
        else:
            at = tiktok if tiktok.startswith("@") else f"@{tiktok}"
            tt_line = f"📲TikTok: {at}"
    else:
        tt_line = "📲TikTok: не указан"

    text = (
        f"🙋‍♀️Имя: {name}\n"
        f"🎮Ник в игре: <code>{nickname}</code>\n"
        f"🔢UID: <code>{uid}</code>\n"
        f"🎂Дата рождения: {bday}\n"
        f"🏙Город: {city}\n"
        f"{tt_line}\n"
        f"🍆Пиписа: {pipisa:.1f} см\n"
        f"📝Девиз: {quote}"
    )
    return text

async def profile_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id, update.effective_user.username, update.effective_user.mention_html())
    u = state["users"].get(uid)
    await update.message.reply_text(render_profile(u), parse_mode="HTML")

async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id, update.effective_user.username, update.effective_user.mention_html())
    context.user_data["profile_answers"] = {}
    await update.message.reply_text("Как тебя зовут? (имя)")
    return STEP_NAME

async def step_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["name"] = update.effective_user.mention_html()
    await update.message.reply_text("Какой у тебя ник в игре?")
    return STEP_NICK

async def step_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["nickname"] = update.message.text.strip()
    await update.message.reply_text("Какой у тебя UID?")
    return STEP_UID

async def step_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["uid"] = update.message.text.strip()
    await update.message.reply_text("Когда у тебя день рождения? (например, 01.01.2000 или 01.01)")
    return STEP_BDAY

async def step_bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["bday"] = update.message.text.strip()
    await update.message.reply_text("Из какого ты города?")
    return STEP_CITY

async def step_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["city"] = update.message.text.strip()
    await update.message.reply_text("Оставь ссылку на TikTok или просто свой ник (@username):")
    return STEP_TIKTOK

async def step_tiktok(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["tiktok"] = update.message.text.strip()
    await update.message.reply_text("Поделись своим девизом или любимой цитатой:")
    return STEP_QUOTE

async def step_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["quote"] = update.message.text.strip()
    suid = str(update.effective_user.id)
    ensure_user(update.effective_user.id, update.effective_user.username, update.effective_user.mention_html())
    stored = state["users"][suid]
    for k, v in context.user_data["profile_answers"].items():
        stored[k] = v
    save_state()
    await update.message.reply_text("Профиль обновлён✅")
    return ConversationHandler.END

# ===================== ПРЕДСКАЗАНИЯ (200 строк) =====================
PREDICTIONS = [
    "Сегодня твой день — даже если облачно☁️",
    "Улыбка решит больше, чем кажется😊",
    "Делай по любви и будет кайф💖",
    "Вселенная сегодня на твоей стороне✨",
    "Ты видишь больше, чем другие — доверься себе👁️",
    "Маленький шаг тоже движение вперёд👣",
    "Слухи остаются слухами — будь выше🕊️",
    "Пусть душа сегодня потанцует💃",
    "Ты — чьё-то «повезло»🍀",
    "Смелость будет вознаграждена🔥",
    "Ты прекрасна уже сейчас, не откладывай жизнь на потом🌸",
    "Твоя мягкость — твоя сила🪷",
    "Сделай доброе дело и получишь больше💫",
    "Смотри шире — возможности рядом🔭",
    "Тебе повезёт в том, что важно именно тебе🎯",
    "Сегодня ты — источник вдохновения для кого-то🌟",
    "Пусть мир сегодня будет к тебе добрее🤍",
    "Найди 10 минут тишины, это изменит день🕯️",
    "Твоя интуиция подскажет верный поворот🧭",
    "Ты умеешь больше, чем думаешь🚀",
    "Сегодня всё получится лучше, чем ожидалось🌈",
    "Счастье уже под боком — заметь его🔎",
    "Побалуй себя маленькой радостью🍰",
    "Вдохни глубже и станет легче🌬️",
    "Ты на верном пути — продолжай идти🛤️",
    "Попроси о помощи и её дадут🤝",
    "Скажи «да» новому шансу🎁",
    "Ты сегодня особенно красивая — сияешь изнутри✨",
    "Твоя улыбка — персональный луч солнца☀️",
    "В твоём взгляде космос — его хочется изучать🌌",
    "Тебе очень идёт твоя мягкость и нежность🪷",
    "Ты идёшь и мир становится эстетичнее🎨",
    "Твоя естественность — лучший макияж💄",
    "Ты выглядишь так, как будто любишь себя и это прекрасно💖",
    "Твоё чувство стиля сегодня на высоте👗",
    "У тебя редкая красота — тёплая и честная🤍",
    "С тобой рядом хочется стать лучше✨",
    "У тебя красивые мысли — они отражаются в глазах👁️",
    "Ты выглядишь так, будто тебе всё по силам🔥",
    "Ты как эстетичный фильм — на тебя хочется смотреть🎞️",
    "Ты светишься и это не хайлайтер✨",
    "Твоя мимика — отдельный вид искусства🎭",
    "Ты вдохновляешь быть бережнее к себе🌿",
    "Твоя красота — это про внутренний порядок и тепло🏡",
    "Ты как утро в выходной: спокойно и прекрасно☕️",
    "С тобой рядом даже зеркала улыбаются🪞",
    "Ты в гармонии — и это заметно🌈",
    "Выбери маленькую цель — и порадуй себя победой🏁",
    "Если страшно — всё равно сделай маленький шаг🐾",
    "Сделай сегодня то, за что завтра скажешь себе спасибо💌",
    "Сохрани энергию для важного — остальное можно отложить🧺",
    "Ты можешь мягко, но уверенно — и это сила🧘",
    "Твоя дисциплина сегодня будет лёгкой и доброй🍃",
    "Сомнения — это шум. Твой голос — важнее🔊",
    "Отпусти перфекционизм — начни как получается🪄",
    "Сделай паузу — и поймёшь, куда идти дальше🛑",
    "Ты заслуживаешь результатов, к которым идёшь🌟",
    "Сконцентрируйся на одном — и увидишь прогресс🎯",
    "Позволь себе ошибаться — это часть пути🧩",
    "Сохраняй темп, но не забывай дышать🌬️",
    "Сравнивай себя только с собой вчера🔁",
    "Ты уже многое прошла — это твой ресурс🧱",
    "Запланируй 15 минут для мечты — это важно💭",
    "Заметь, сколько уже сделано — это мотивирует📈",
    "Ты не обязана быть идеальной — просто будь собой🤍",
    "Доверься процессу — он ведёт куда нужно🗺️",
    "Сегодня хороший день для старта нового шага🚀",
    "Ты — чьё-то вдохновение сегодня🌟",
    "Красота твоих действий важнее мнений других💫",
    "Подари себе спокойный вечер — ты заслужила🕯️",
    "Мир дружелюбнее, чем кажется — посмотри вокруг👀",
    "Твоё сердце знает ответы — прислушайся💓",
    "Тепло, которое ты даёшь, вернётся сильнее🔥",
    "У тебя получится лучше, чем ты думаешь✅",
    "Ласковость к себе — не каприз, а опора🫶",
    "Сделай по любви — и всё сложится🌸",
    "Оставь место для чуда — оно любит тишину✨",
    "Ты — ценность без условий💎",
    "Никто не имеет права гасить твой свет🕯️",
    "То, что твоё, найдёт тебя🔒",
    "Будь бережна к себе так же, как к лучшей подруге🤍",
    "Ты — хороший человек, этого достаточно🫶",
    "Маленькая забота о себе — большая победа🏆",
    "Слушай тело — оно мудро🧘‍♀️",
    "Ты умеешь замечать красоту — это дар🎨",
    "Сегодня будет повод искренне улыбнуться🙂",
    "Выбирай людей, которые выбирают тебя🤝",
    "Не бойся просить — ты достойна поддержки💌",
    "Твоя история уже прекрасна, а будет ещё лучше📖",
    "Отпусти чужие ожидания — тебе станет легче🎈",
    "Говори «нет» спокойно и уверенно⛔️",
    "Ты не обязана быть удобной — будь настоящей🌹",
    "С каждым шагом ты ближе к желаемому🧭",
    "Разреши себе отдых без чувства вины🛌",
    "Сегодня тебе повезёт там, где ты смелее всего🔥",
    "Ты — мягкая сила, которая меняет мир🕊️",
    "Твоя доброта — огромная ценность🤍",
    "Ты умеешь слушать себя — это суперсила🦸‍♀️",
    "Небо сегодня на твоей стороне☀️",
    "Ты красивая, талантливая и достойная всего хорошего💖",
    "Пусть сегодня будет много тёплых слов и маленьких чудес✨",
    "У тебя есть право замедлиться⏸️",
    "Ты — та, кто справится. Всегда💪",
    "Стань себе лучшей подругой — это изменит всё💞",
    "Доверься процессу — он тебя не подведёт🧭",
    "Ты заслуживаешь мягкости и уважения🤍",
    "Сегодня сделай что-то приятное только для себя🎁",
    "Ты — вдохновение для тех, кто рядом🌟",
    "Смех сегодня продлит день — найди повод😂",
    "Ты уже достаточно — не нужно доказывать⚖️",
    "Мир станет добрее от твоей доброты🫰",
    "Пусть твоё сердце сегодня будет спокойно💗",
    "Сделай паузу, посмотри в окно — вдохновение рядом🌤️",
    "Ты умеешь любить — начни с себя💘",
    "Ничего страшного в том, чтобы не успеть всё🕰️",
    "Ты — не сравнение. Ты — ты💫",
    "Сегодня почувствуешь, что всё становится на места🧩",
    "Самая сильная — это ты, когда добра к себе🤍",
    "Улыбнись себе в зеркале — ты классная🪞",
    "Твоя честность притягивает правильных людей🧲",
    "Пусть день будет лёгким и тёплым🫧",
    "Ласковые слова себе сегодня — мастхэв💌",
    "Ты всё делаешь вовремя — в своём ритме⏳",
    "Сделай выбор в пользу себя — это не эгоизм🌷",
    "Ты — как утро в любимом городе☕️",
    "С тобой становится уютнее всем, даже кошкам🐾",
    "Даже маленькие усилия складываются в большое📈",
    "Сегодня ты — героиня своей истории🎬",
    "Вдохновение придёт, когда перестанешь спешить🕊️",
    "Ты достойна самых бережных объятий🫂",
    "Скажи себе «я справлюсь» — и так и будет✅",
    "Будь рядом с собой — это главное🤍",
    "Пусть всё нужное приходит легко, а ненужное уходит🌬️",
    "Ты — свет. Свети✨",
    "Твоё спокойствие — самая красивая одежда👗",
    "Жизнь сегодня подмигнёт тебе😉",
    "Твоя доброта — не слабость, а выбор💪",
    "Вдохни надежду — выдохни сомнение🌬️",
    "Ты — причина чьей-то улыбки сегодня🙂",
    "Пусть мир обнимет тебя мягко🫶",
    "Ты уже на много шагов впереди себя вчерашней➡️",
    "Сделай сегодня что-то маленькое и важное для души🕯️",
    "Ты прекрасна, и точка💖",
    "Сердце знает, где ему хорошо💓",
    "Удача любит твою смелость🍀",
    "Твоя нежность сильнее любых бурь🌪️",
    "Сегодня будет тепло — даже если пасмурно☁️",
    "Ты — человек-лучик, помни это☀️",
    "Выбирай себя каждый раз🫶",
    "Ты не обязана быть продуктивной, чтобы быть ценной💎",
    "Жизнь встанет на твою сторону, когда встанешь на свою✨",
    "Ты — чудо, которое уже случилось🌟",
    "Разреши себе радоваться без повода🎈",
    "Твои желания — не каприз, а навигатор🧭",
    "Твои границы — твоя забота о себе🛡️",
    "День подарит красивую встречу или мысль💡",
    "Ты — добрая сила, которая меняет реальность🕊️",
    "Пусть сегодня всё будет по любви💘",
    "Ты важна для мира именно такой, какая ты есть🤍",
    "Сделай себе чай и выдохни🍵",
    "Ты умеешь быть опорой — начни с себя🧱",
    "Красота внутри делает красивее всё вокруг🌸",
    "Сегодня всё нужное найдёт тебя само🧲",
    "Ты — не задача для исправления, ты — жизнь для проживания🌿",
    "Пусть твоя нежность вернётся к тебе сильнее💞",
    "Сегодня день, когда всё возможно⭐",
    "Ты уже достаточно стараешься — можно и отдохнуть🛌",
    "На каждом шаге тебя ждёт что-то хорошее🍀",
    "Ты — та, кто может мягко, но уверенно менять мир🌍",
    "Твоё добро всегда имеет значение🤍",
    "Ты — целая. Всегда💫",
    "Пусть сегодняшний день принесёт лёгкость и ясность🔆",
    "Ты заслуживаешь заботы — в первую очередь своей🫶",
    "Сегодня ты увидишь подтверждение своей силы💪",
    "Ты — красота, нежность и уверенность в одном✨",
    "Мир сегодня поддержит твои добрые намерения🕊️",
    "Ты — любовь. И точка💖",
    "Пусть любое «надо» станет чуть мягче и теплее🫧",
    "Ты можешь всё, но выбирай то, что бережно к тебе🤍",
    "Сегодня будет повод сказать «спасибо» жизни🙏",
    "Ты — уют и свет для себя и других🕯️",
    "Доброта к себе — твой лучший план на день📋",
    "Ты — важная, нужная и очень ценная💎",
    "Пусть сегодня будет больше тишины и мира внутри🌿",
    "Ты смелая — даже когда этого не замечаешь🔥",
    "Сделай шаг к мечте — любой, но сегодня🚶‍♀️",
    "Ты — пример нежной силы🦋",
    "Мир улыбается тебе — улыбнись в ответ🙂",
    "Ты — чудесная. Поверь себе ещё раз✨",
    "Пусть будет легко выбирать то, что тебе хорошо🫶",
    "Ты — дом для себя. Береги этот дом🏡",
    "Жизнь соображает под тебя — просто дай ей знак🪄",
    "Нежность к себе — это тоже дисциплина🧘‍♀️",
    "Ты способна создавать красоту из ничего🎨",
    "Пусть в сердце будет тихо и тепло🕯️",
    "Ты — настоящее «повезло» для этого мира🍀",
    "Сегодня тебя ждёт маленькая радость🎁",
    "Ты — сильная и хрупкая одновременно, и это прекрасно💖",
    "Будь бережной — и мир ответит тем же🤍",
    "Ты — вдохновляющий пример для самой себя🌟",
    "Всё получится. Обязательно✅",
]

# ===================== КОМПЛИМЕНТЫ (45 строк) =====================
COMPLIMENTS = [
    "Ты очень бережно относишься к людям — это видно🤟",
    "В тебе много света, с тобой теплее✨",
    "Ты красивая так, как сама решаешь быть💋",
    "С тобой хочется дружить и смеяться😂",
    "Ты из тех, кто умеет любить искренне💖",
    "Ты создаёшь уют даже одним сообщением🕯️",
    "В твоих глазах всегда немного космоса🌌",
    "Ты вдохновляешь быть нежнее к себе🫶",
    "С тобой безопасно быть собой🤍",
    "Ты как чай с мёдом — согреваешь🍯",
    "С тобой легче дышится🌿",
    "Твоя улыбка — лучший фильтр дня🙂",
    "Ты умеешь слушать — это редкость👂",
    "Твой юмор лечит лучше таблеток😌",
    "Ты очень талантлива, просто иногда забываешь об этом💫",
    "Твоя поддержка — это суперсила🦸‍♀️",
    "Ты красиво говоришь даже о сложном🎀",
    "С тобой всё становится по-настоящему живым🌷",
    "Ты очень ценная — и точка💎",
    "С тобой хочется делиться радостью и тишиной🕊️",
    "Ты — человек-дом для близких🏡",
    "Ты — про доброту без громких слов🤍",
    "Твоя мягкость обезоруживает🪷",
    "Ты умеешь видеть хорошее — и даришь это другим🌈",
    "Твоё сердце большое и тёплое💓",
    "Ты бережно обращаешься с чувствами — это бесценно💌",
    "Ты умеешь быть искренней — это редкий дар💎",
    "С тобой рядом хочется быть лучше🌟",
    "Ты — красивый характер, а не только лицо💖",
    "Ты очень чуткая — настоящий подарок людям🎁",
    "Ты умеешь успокаивать одним сообщением🫶",
    "Ты — эстетика и тепло в одном✨",
    "С тобой всё по-настоящему и без масок🎭",
    "Ты мягкая, но очень сильная внутри💪",
    "Ты — душевный человек, таких мало🤍",
    "Твои слова часто попадают прямо в сердце🎯",
    "Ты прекрасна просто тем, что есть🌸",
    "Ты — человек, рядом с которым хочется улыбаться🙂",
    "Ты вдохновляешь верить в себя🌟",
    "Ты — тот самый тёплый свет, который нужен всем🕯️",
    "В тебе чувствуется глубина и нежность🪷",
    "Ты умеешь поддержать вовремя💌",
    "Ты — подарок для этого чата🎀",
    "Ты делаешь мир немного добрее каждый день🕊️",
    "Ты — удивительно красивая и изнутри, и снаружи💖",
]

# ===================== /predskaz =====================
async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.mention_html())
    suid = str(user.id)
    u = state["users"][suid]
    if u.get("last_prediction") == today_str():
        await update.message.reply_text("🔮Предсказание уже было сегодня")
        return
    u["last_prediction"] = today_str()
    save_state()
    await update.message.reply_text(f"🔮{random.choice(PREDICTIONS)}")

# ===================== /compliment =====================
async def compliment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = update.effective_user
    ensure_user(me.id, me.username, me.mention_html())
    if update.message and update.message.reply_to_message:
        ru = update.message.reply_to_message.from_user
        ensure_user(ru.id, ru.username, ru.mention_html())
        target = display_user(ru.id)
    elif context.args:
        target = context.args[0]
    else:
        pool = [uid for uid in state.get("known_users", []) if uid != me.id]
        if not pool:
            await update.message.reply_text("Сегодня комплимент всем в чате💐")
            return
        target = display_user(random.choice(pool))
    phrase = random.choice(COMPLIMENTS)
    await update.message.reply_text(f"{me.mention_html()} говорит {target}: {phrase}", parse_mode="HTML")

# ===================== /hugs =====================
HUGS_POOL = [
    "🤗{a} крепко обняла {b} — тепло доставлено по адресу🧸",
    "💞{a} нежно прижалась к {b} — пусть тревоги тают🌷",
    "🥰{a} согрела {b} своими обнимашками — зарядилась любовью",
    "🫶{a} и {b} — сегодня самый милый дуэт",
    "Кто не обнимется — тот не играет в кастомке",
    "🫂Токсиков тоже иногда обнимают… по голове… табуреткой🙃",
    "Передаю мягкость, заботу и печеньку🍪 — {a} → {b}",
    "Крепко-крепко и очень нежно — трепещи, грусть🫂 {a} обняла {b}",
    "Пусть тревоги уменьшаются после этих объятий🌸 {a} для {b}",
]

async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = update.effective_user
    ensure_user(me.id, me.username, me.mention_html())
    if update.message and update.message.reply_to_message:
        ru = update.message.reply_to_message.from_user
        ensure_user(ru.id, ru.username, ru.mention_html())
        target = display_user(ru.id)
        await update.message.reply_text(f"🤗{me.mention_html()} отправила объятия {target}! Тепло доставлено🧸", parse_mode="HTML")
        return
    if context.args:
        await update.message.reply_text(f"🤗{me.mention_html()} отправила объятия {context.args[0]}! Тепло доставлено🧸", parse_mode="HTML")
        return
    pool = [uid for uid in state.get("known_users", []) if uid != me.id]
    if not pool:
        await update.message.reply_text("Обнимашки для всех в чате🫂")
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

# ===================== /lesbi =====================
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = update.effective_user
    ensure_user(me.id, me.username, me.mention_html())
    pool = list(set(state.get("known_users", [])))
    if len(pool) < 2:
        await update.message.reply_text("Недостаточно участниц для пары")
        return
    if state["last_lesbi_date"] == today_str() and state.get("last_lesbi_pair"):
        a, b = state["last_lesbi_pair"]
        await update.message.reply_text(f"👭Пара дня уже выбрана: {display_user(a)} + {display_user(b)}💞", parse_mode="HTML")
        return
    a, b = random.sample(pool, 2)
    state["last_lesbi_date"] = today_str()
    state["last_lesbi_pair"] = [a, b]
    save_state()
    lines = [
        "🌈Сегодняшняя лесби-пара: {a} и {b}💋",
        "🫶Кто бы мог подумать! {a} и {b} — пара дня",
        "💘Амур попал точно в цель! {a} и {b} теперь вместе😍",
        "💞Любовь витает в воздухе: {a} + {b} = ❤️",
    ]
    msg = random.choice(lines).format(a=display_user(a), b=display_user(b))
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

# ===================== /role =====================
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
    "богиня флирта💋","дева хаоса🫦",
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
    "девочка с планом📋",
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

def _pick_user_from_arg_or_random(me: int, args, update: Update) -> str:
    if update.message and update.message.reply_to_message:
        ru = update.message.reply_to_message.from_user
        ensure_user(ru.id, ru.username, ru.mention_html())
        return display_user(ru.id)
    if args:
        return args[0]
    pool = [uid for uid in state.get("known_users", []) if uid != me]
    if not pool:
        return display_user(me)
    return display_user(random.choice(pool))

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = update.effective_user
    ensure_user(me.id, me.username, me.mention_html())
    target_disp = _pick_user_from_arg_or_random(me.id, context.args, update)
    await update.message.reply_text(f"{target_disp} сегодня {random.choice(ROLES)}", parse_mode="HTML")

# ===================== /pipisa (1 раз/день, граница -50.0) =====================
def _rand_delta():
    d = round(random.uniform(-10.0, 10.0), 1)
    if d == 0.0:
        d = 0.1 if random.random() > 0.5 else -0.1
    return d

async def pipisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    ensure_user(user.id, user.username, user.mention_html())
    suid = str(user.id)
    u = state["users"][suid]
    if u.get("last_pipisa") == today_str():
        await update.message.reply_text("Пипису можно растить/мерить только раз в день🌱")
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
            "Она стремится к вершинам📈",
            "Вперед и выше, король пипис гордится тобой🥳",
            "Так растёт только легенда🌟",
            "Сияет и радует хозяйку✨",
        ])
        msg = f"🍆Пиписа выросла на {delta:.1f} см! {phrase} Твоя пиписа теперь {new_val:.1f} см."
    else:
        phrase = random.choice([
            "Прям как у твоего бывшего...",
            "Иногда и героям нужен отдых🌧️",
            "Не ростраюйся🫂",
            "Подрочи и пиписа увеличится🌈",
        ])
        msg = f"🍆Оу… пиписа уменьшилась на {abs(delta):.1f} см. {phrase} Твоя пиписа теперь {new_val:.1f} см."
    await update.message.reply_text(msg, parse_mode="HTML")

# ===================== /duel (до 3 раз/день, сила влияет на шанс) =====================
def _duel_amount():
    return round(random.uniform(0.5, 5.0), 1)

async def duel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = update.effective_user
    ensure_user(me.id, me.username, me.mention_html())
    suid = str(me.id)
    u_me = state["users"][suid]

    # лимит 3/день
    if u_me.get("duel_used_on") != today_str():
        u_me["duel_used_on"] = today_str()
        u_me["duel_uses"] = 0
    if u_me["duel_uses"] >= 3:
        await update.message.reply_text("Сегодня лимит дуэлей исчерпан (3/день)⚔️")
        return

    # цель: reply или первый аргумент как @юзер (строка)
    target_id = None
    if update.message and update.message.reply_to_message:
        target_user = update.message.reply_to_message.from_user
        ensure_user(target_user.id, target_user.username, target_user.mention_html())
        target_id = target_user.id
    elif context.args:
        # попытаемся найти по username среди известных
        arg = context.args[0].lstrip("@")
        for uid_str, data in state["users"].items():
            uname = data.get("username", "").lstrip("@")
            if uname and uname.lower() == arg.lower():
                target_id = int(uid_str)
                break
    if not target_id:
        await update.message.reply_text("Отметь соперницу ответом на сообщение или укажи @юзер после команды")
        return
    if target_id == me.id:
        await update.message.reply_text("С собой дуэлиться нельзя🙂")
        return

    ensure_user(target_id, state["users"].get(str(target_id), {}).get("username"), state["users"].get(str(target_id), {}).get("name"))
    u_op = state["users"][str(target_id)]

    # шанс победы: 50% + (power_me - power_op)*5%, ограничим 10..90%
    power_me = int(u_me.get("pipisa_power", 0))
    power_op = int(u_op.get("pipisa_power", 0))
    win_chance = 0.5 + (power_me - power_op) * 0.05
    win_chance = max(0.1, min(0.9, win_chance))

    amount = _duel_amount()
    me_wins = random.random() < win_chance

    if me_wins:
        u_me["pipisa"] = round(float(u_me.get("pipisa", 0.0)) + amount, 1)
        u_op["pipisa"] = round(float(u_op.get("pipisa", 0.0)) - amount, 1)
        if u_op["pipisa"] < -50.0:
            u_op["pipisa"] = -50.0
        text = f"⚔️Дуэль! {display_user(me.id)} победила {display_user(target_id)} и отвоевала {amount:.1f} см. Твоя пиписа теперь {u_me['pipisa']:.1f} см."
    else:
        u_me["pipisa"] = round(float(u_me.get("pipisa", 0.0)) - amount, 1)
        if u_me["pipisa"] < -50.0:
            u_me["pipisa"] = -50.0
        u_op["pipisa"] = round(float(u_op.get("pipisa", 0.0)) + amount, 1)
        text = f"⚔️Дуэль! {display_user(target_id)} победила {display_user(me.id)} и отвоевала {amount:.1f} см. Твоя пиписа теперь {u_me['pipisa']:.1f} см."

    # рост силы за участие
    u_me["pipisa_power"] = int(u_me.get("pipisa_power", 0)) + 1
    u_op["pipisa_power"] = int(u_op.get("pipisa_power", 0)) + 1

    u_me["duel_uses"] = int(u_me.get("duel_uses", 0)) + 1
    save_state()
    await update.message.reply_text(text, parse_mode="HTML")

# ===================== РЕЙТИНГИ =====================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id, update.effective_user.username, update.effective_user.mention_html())
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)[:5]
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще🌱")
        return
    text = "🏆ТОП-5 пипис клана:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or display_user(int(uid))}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id, update.effective_user.username, update.effective_user.mention_html())
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще🌱")
        return
    text = "📊Полный рейтинг пипис:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or display_user(int(uid))}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ===================== ДР (ежедневно) =====================
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
            name = u.get("name") or display_user(int(suid))
            text = f"🎂Сегодня день рождения у {name}! Пожелаем счастья, любви и побед🥳"
            try:
                await context.bot.send_message(chat_id=CHAT_ID, text=text, parse_mode="HTML")
            except Exception as e:
                logger.warning(f"Не удалось отправить поздравление: {e}")

# ===================== РЕГИСТРАЦИЯ И ЗАПУСК =====================
def build_application():
    app = ApplicationBuilder().token(TOKEN).build()

    # привет/прощание
    app.add_handler(ChatMemberHandler(greet_or_bye, ChatMemberHandler.CHAT_MEMBER))

    # профиль — пошагово
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
    app.add_handler(CommandHandler("profile", profile_cmd))

    # базовые команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("about", about))
    app.add_handler(CommandHandler("info", info_cmd))
    app.add_handler(CommandHandler("rules", rules))

    # фан
    app.add_handler(CommandHandler("pipisa", pipisa))
    app.add_handler(CommandHandler("duel", duel))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("hugs", hugs))
    app.add_handler(CommandHandler("lesbi", lesbi))
    app.add_handler(CommandHandler("role", role))
    app.add_handler(CommandHandler("compliment", compliment))

    # предсказания
    app.add_handler(CommandHandler("predskaz", predskaz))

    # ежедневные поздравления с ДР
    app.job_queue.run_daily(birthday_job, time(hour=9, minute=0))

    # самый последний — «тихое» запоминание всех
    app.add_handler(MessageHandler(filters.ALL, track_seen_user))

    return app

if __name__ == "__main__":
    application = build_application()
    print("OnlyGirls bot запущен…")
    application.run_polling(close_loop=False)
