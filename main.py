# -*- coding: utf-8 -*-
import json
import logging
import random
from datetime import datetime, date, time, timedelta
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
#     "name", "nickname", "uid", "bday", "city",
#     "tiktok", "joined_date", "quote",
#     "pipisa", "last_pipisa", "last_prediction", "last_tarot",
#     "married_to"
#   }
# }
# known_users: [int, ...]  # все, кого знаем (вступили в чат/писали боту)
# proposals: { target_id(str): proposer_id(int) }
# divorce_requests: { partner_id(str): requester_id(int) }
# last_lesbi_date: "YYYY-MM-DD"
# last_lesbi_pair: [user_id_a(int), user_id_b(int)]
state = {
    "users": {},
    "known_users": [],
    "proposals": {},
    "divorce_requests": {},
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

def ensure_user(user_id: int):
    suid = str(user_id)
    if suid not in state["users"]:
        state["users"][suid] = {
            "name": "",
            "nickname": "",
            "uid": "",
            "bday": "",
            "city": "",
            "tiktok": "",
            "joined_date": "",  # установим при первом сохранении профиля
            "quote": "",
            "pipisa": 0.0,
            "last_pipisa": None,
            "last_prediction": None,
            "last_tarot": None,
            "married_to": None,
        }
    if user_id not in state.get("known_users", []):
        state["known_users"].append(user_id)

def tg_link_from_id(user_id: int, text: str = "участница") -> str:
    return f'<a href="tg://user?id={user_id}">{text}</a>'

def display_user(user_id: int) -> str:
    u = state["users"].get(str(user_id))
    if u and u.get("name"):
        return u["name"]  # здесь уже mention_html
    # иначе кликабельная ссылка по id
    return tg_link_from_id(user_id, "девочка")

def is_url(s: str) -> bool:
    return s.startswith("http://") or s.startswith("https://")

# ===================== ПРИВЕТСТВИЕ НОВЫХ =====================
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    old = cmu.old_chat_member.status
    new = cmu.new_chat_member.status
    if (old in ("left", "kicked")) and (new in ("member", "administrator", "creator")):
        user = cmu.new_chat_member.user
        ensure_user(user.id)
        save_state()
        text = (
            f"Добро пожаловать, {user.mention_html()}❣️ "
            f'Ознакомься пожалуйста с правилами клана '
            f'(<a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a>)🫶 '
            f"Важная информация всегда в закрепе❗️ Клановая приставка: ঔ"
        )
        await context.bot.send_message(chat_id=cmu.chat.id, text=text, parse_mode="HTML")

# ===================== /START и /ABOUT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id)
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
        "/tarot — карта Таро (1 раз в день)\n"
        "/hugs [@юзер] — обнимашки (для всех или указанного)\n"
        "/lesbi — лесби-пара дня (1 раз в день)\n"
        "/love @юзер — сделать предложение\n"
        "/acceptlove — принять предложение\n"
        "/declinelove — отклонить предложение\n"
        "/divorce — запрос на развод\n"
        "/acceptdivorce — подтвердить развод\n"
        "/rules — правила клана (ссылка)"
    )

# ===================== /RULES (ссылка) =====================
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Котик, правила клана <a href="https://telegra.ph/Pravila-klana-%E0%A6%90OnlyGirls%E0%A6%90-05-29">здесь</a> 🫶',
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
    joined = u.get("joined_date") or ""
    quote = u.get("quote") or "—"
    pipisa = float(u.get("pipisa") or 0.0)

    # В чате N дней
    days_line = "не указано"
    if joined:
        try:
            d0 = datetime.strptime(joined, "%Y-%m-%d").date()
            days_line = f"{(date.today() - d0).days} дней"
        except Exception:
            days_line = "не указано"

    # TikTok строка
    if tiktok:
        if is_url(tiktok):
            tt_line = f'📲 TikTok: <a href="{tiktok}">TikTok</a>'
        else:
            at = tiktok if tiktok.startswith("@") else f"@{tiktok}"
            tt_line = f"📲 TikTok: {at}"
    else:
        tt_line = "📲 TikTok: не указан"

    married_to = u.get("married_to")
    married_line = f"💍 В браке с {married_to}\n" if married_to else ""

    text = (
        f"🙋‍♀️ Имя: {name}\n"
        f"🎮 Ник в игре: <code>{nickname}</code>\n"
        f"🔢 UID: <code>{uid}</code>\n"
        f"🎂 Дата рождения: {bday}\n"
        f"🏙 Город: {city}\n"
        f"{tt_line}\n"
        f"📆 В чате: {days_line}\n"
        f"🍆 Пиписа: {pipisa:.1f} см\n"
        f"{married_line}"
        f"📝 Девиз: {quote}"
    )
    return text

async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"].get(uid)
    await update.message.reply_text(render_profile(u), parse_mode="HTML")

async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id)
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
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)

    # Переносим ответы в хранилище
    stored = state["users"][uid]
    for k, v in context.user_data["profile_answers"].items():
        stored[k] = v

    # Если нет joined_date — поставить сегодня
    if not stored.get("joined_date"):
        stored["joined_date"] = today_str()

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
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]

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
        text += f"{i}. {u.get('name') or tg_link_from_id(int(uid), uid)}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")

async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще 🌱")
        return
    text = "📊 Полный рейтинг пипис:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or tg_link_from_id(int(uid), uid)}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")

# ===================== ПРЕДСКАЗАНИЯ =====================
PREDICTIONS = [
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
    # ... можешь расширить список по желанию
]

async def predskaz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]
    if u.get("last_prediction") == today_str():
        await update.message.reply_text("🔮 Предсказание уже было сегодня!")
        return
    u["last_prediction"] = today_str()
    save_state()
    await update.message.reply_text(f"🔮 {random.choice(PREDICTIONS)}")

# ===================== ТАРО =====================
TAROT = [
    {
        "name": "Сила 🦁",
        "upright_meaning": "смелость, терпение, уверенность",
        "reversed_meaning": "сомнение, страх, внутреннее напряжение",
        "upright_motto": "Я мягко сильна.",
        "reversed_motto": "Я признаю страх — и иду дальше.",
        "upright_advice": "Сегодня действуй из спокойной уверенности. Твоя сила в мягкости и постоянстве.",
        "reversed_advice": "Время признать усталость и восстановить ресурс. Поддержка рядом — попроси о помощи.",
    },
    {
        "name": "Звезда 🌟",
        "upright_meaning": "надежда, вдохновение, исцеление",
        "reversed_meaning": "пессимизм, истощение, сомнение",
        "upright_motto": "Во мне свет.",
        "reversed_motto": "Я зажигаю свой свет заново.",
        "upright_advice": "Надежда — твой компас. Делай маленькие шаги и верь в лучшее.",
        "reversed_advice": "Пора напомнить себе, что ты не одна. Найди источник вдохновения и заботы.",
    },
    {
        "name": "Солнце ☀️",
        "upright_meaning": "радость, успех, просветление",
        "reversed_meaning": "самокритика, упрямство, задержки",
        "upright_motto": "Я выбираю радость.",
        "reversed_motto": "Я позволяю себе теплоту.",
        "upright_advice": "Поделись своим светом. День для ясности и искренности.",
        "reversed_advice": "Уменьши давление на себя. Радость придёт, если дать ей место.",
    },
    # ... при желании добавь остальные арканы в таком же формате
]

async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]
    if u.get("last_tarot") == today_str():
        await update.message.reply_text("🃏 Расклад Таро доступен раз в день!")
        return

    card = random.choice(TAROT)
    reversed_flag = random.choice([True, False])

    if reversed_flag:
        position = "в перевёрнутом значении"
        meaning = card["reversed_meaning"]
        motto = card["reversed_motto"]
        advice = card["reversed_advice"]
    else:
        position = "в прямом значении"
        meaning = card["upright_meaning"]
        motto = card["upright_motto"]
        advice = card["upright_advice"]

    u["last_tarot"] = today_str()
    save_state()

    text = (
        f"🃏 Тебе выпала карта: <b>{card['name']}</b> ({position})\n"
        f"Значение: {meaning}\n"
        f"Девиз на день: «{motto}»\n"
        f"Направление: {advice}"
    )
    await update.message.reply_text(text, parse_mode="HTML")

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
    ensure_user(update.effective_user.id)
    me = update.effective_user
    if context.args:
        # Обнимаем указанного @юзера как текст
        target = context.args[0]
        msg = random.choice([
            f"🤗 {me.mention_html()} обняла {target}! Тепло доставлено 🧸",
            f"💞 {me.mention_html()} отправила объятия {target}. Всё будет хорошо 🌷",
        ])
        await update.message.reply_text(msg, parse_mode="HTML")
        return

    # Рандомная цель из known_users (кроме себя)
    pool = [uid for uid in state.get("known_users", []) if uid != me.id]
    if not pool:
        await update.message.reply_text("Обнимашки для всех в чате! 🫂")
        return
    target_id = random.choice(pool)
    a = me.mention_html()
    b = display_user(target_id)
    tpl = random.choice(HUGS_POOL)
    # Шаблон может не содержать {a}/{b} (две «фиксированные» фразы выше)
    if "{a}" in tpl or "{b}" in tpl:
        text = tpl.format(a=a, b=b)
    else:
        text = f"{a} обняла {b} — {tpl}"
    await update.message.reply_text(text, parse_mode="HTML")

# ===================== ЛЕСБИ-ПАРА (независимо от профиля) =====================
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Берём всех, кого знаем
    pool = list(set(state.get("known_users", [])))
    # Должно быть минимум двое
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

# ===================== СВАДЬБЫ / РАЗВОДЫ =====================
async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи, кому предложение: /love @username")
        return
    target_username = context.args[0].lstrip("@")
    proposer = update.effective_user.id
    ensure_user(proposer)

    # Пытаемся найти target по username в сохранённых name (mention_html) — хак: ищем в тексте
    target_id = None
    for suid, u in state["users"].items():
        if u.get("name") and target_username in u["name"]:
            target_id = int(suid)
            break

    if not target_id:
        await update.message.reply_text("Не нашла участницу с таким username в профилях. Попроси её сделать /editprofile.")
        return

    # Проверка браков
    if state["users"][str(proposer)].get("married_to"):
        await update.message.reply_text("Ты уже в браке 💍")
        return
    if state["users"][str(target_id)].get("married_to"):
        await update.message.reply_text("Участница уже в браке 💍")
        return

    state["proposals"][str(target_id)] = proposer
    save_state()
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"💍 {update.effective_user.mention_html()} сделала предложение @{target_username}! "
             f"Ответ — /acceptlove или /declinelove",
        parse_mode="HTML"
    )

async def acceptlove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = str(update.effective_user.id)
    if me not in state["proposals"]:
        await update.message.reply_text("Нет активного предложения для тебя.")
        return
    proposer = state["proposals"].pop(me)
    ensure_user(proposer)
    ensure_user(int(me))
    # Ставим брачные связи (по отображаемому имени)
    state["users"][str(proposer)]["married_to"] = display_user(int(me))
    state["users"][me]["married_to"] = display_user(proposer)
    save_state()

    lines = [
        "💍 {a} и {b} теперь официально жена и жена! Поздравляем! 🎉",
        "👰‍♀️👰‍♀️ Сыграли свадьбу: {a} + {b} = 💒 Любовь!",
        "🥂 Появилась новая семейная пара: {a} & {b}! Пусть будет счастье! 🫶",
        "🎊 {a} и {b} теперь супруги в нашем клане! Нежности и обнимашек! 🥰",
    ]
    msg = random.choice(lines).format(a=display_user(proposer), b=display_user(int(me)))
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

async def declinelove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = str(update.effective_user.id)
    if me not in state["proposals"]:
        await update.message.reply_text("Нет активного предложения для тебя.")
        return
    state["proposals"].pop(me)
    save_state()
    await update.message.reply_text("Предложение отклонено.")

async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = str(update.effective_user.id)
    ensure_user(int(me))
    my = state["users"][me]
    if not my.get("married_to"):
        await update.message.reply_text("Ты не в браке.")
        return

    # Находим партнёрку по name (совпадение строк)
    partner_id = None
    for suid, u in state["users"].items():
        if u.get("name") and u["name"] == my["married_to"]:
            partner_id = int(suid)
            break
    if not partner_id:
        await update.message.reply_text("Не нашла партнёрку в базе. Обратитесь к админам.")
        return

    state["divorce_requests"][str(partner_id)] = int(me)
    save_state()
    await update.message.reply_text("Запрос на развод отправлен. Партнёрке нужно выполнить /acceptdivorce.")

async def acceptdivorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = str(update.effective_user.id)
    if me not in state["divorce_requests"]:
        await update.message.reply_text("Нет активного запроса на развод.")
        return
    other = state["divorce_requests"].pop(me)
    if str(other) in state["users"]:
        state["users"][str(other)]["married_to"] = None
    if me in state["users"]:
        state["users"][me]["married_to"] = None
    save_state()
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"💔 Развод! {display_user(other)} и {display_user(int(me))} расстались.",
        parse_mode="HTML"
    )

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
    # Ежедневно пробегаем всех пользователей и поздравляем именинников
    today = date.today()
    for suid, u in state["users"].items():
        dm = _parse_day_month(u.get("bday", ""))
        if not dm:
            continue
        d, m = dm
        if d == today.day and m == today.month:
            # Поздравляем в общий чат
            name = u.get("name") or tg_link_from_id(int(suid), "девочка")
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

    # Фан
    app.add_handler(CommandHandler("pipisa", pipisa))
    app.add_handler(CommandHandler("top5", top5))
    app.add_handler(CommandHandler("rating", rating))
    app.add_handler(CommandHandler("hugs", hugs))
    app.add_handler(CommandHandler("lesbi", lesbi))

    # Предсказания и таро
    app.add_handler(CommandHandler("predskaz", predskaz))
    app.add_handler(CommandHandler("tarot", tarot))

    # Свадьбы/разводы
    app.add_handler(CommandHandler("love", love))
    app.add_handler(CommandHandler("acceptlove", acceptlove))
    app.add_handler(CommandHandler("declinelove", declinelove))
    app.add_handler(CommandHandler("divorce", divorce))
    app.add_handler(CommandHandler("acceptdivorce", acceptdivorce))

    # JobQueue — поздравления с ДР (каждое утро в 09:00 по серверу)
    app.job_queue.run_daily(birthday_job, time(hour=9, minute=0))

    return app

if __name__ == "__main__":
    application = build_application()
    print("OnlyGirls bot запущен…")
    application.run_polling(close_loop=False)
