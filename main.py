# -*- coding: utf-8 -*-
import json
import logging
import random
from datetime import datetime, date
from pathlib import Path

from telegram import (
    Update, InlineKeyboardButton, InlineKeyboardMarkup
)
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, ChatMemberHandler,
    CallbackQueryHandler, ConversationHandler, ContextTypes, filters
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
# users: { user_id: {
#   "name", "nickname", "uid", "bday", "city", "social", "joined_date",
#   "quote", "pipisa", "last_pipisa", "last_prediction", "last_tarot",
#   "married_to"
# } }
# proposals: { target_id: proposer_id }
# divorce_requests: { partner_id: requester_id }
# last_lesbi_date: "YYYY-MM-DD"
# last_lesbi_pair: [user_id_a, user_id_b]
state = {
    "users": {},
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


# ===================== ТЕКСТ ПРАВИЛ (РОВНО КАК ТЫ ДАЛА) =====================
RULES_TEXT = """❶. Каждая участница клана обязана:

1.1 Знать и соблюдать правила клана;

1.2 Установить клановую приставку ঔ (в конце ника);

1.3 Учавствовать в кастомках, скримах и совместных играх с соклановцами;

1.4 Быть активной в чате, голосовать в опросах, участвовать в кастомках,  реагировать на просьбы соклановцев и администрации;

1.5 По возможности помогать соклановцам и не допускать внутриклановых конфликтов;

1.6 Заботиться о репутации клана (если ты токсик, то пожалуйста, в пределах разумного).

❷. Девочки состоящие в клане имеют право: 

2.1 Договариваться о клановых битвах от имени клана, предварительно предупредив об этом администрацию;

2.2 Предлагать свои идеи для улучшения внутриклановой обстановки и поднятия репутации клана. 

❸. Участницам клана запрещается:

3.1 Разглашать внутреннюю информацию клана, переписки из кланового чата;

3.2 Оскорблять соклановцев(!);

3.3 Создавать конфликты на тему политики, религии и т.п.;

3.4 Любыми действиями портить репутацию клана.

❹. Исключение и наказание: 

4.1 Любая участница клана вправе требовать о наказании или исключении из клана любой другой участницы, которая:

- не выполняет в полной мере свои обязанности;

- своими действиями (бездействием) делает невозможной успешную деятельность клана или существенно её затрудняет;

- не выполняет решения, просьбы и распоряжения, принятые администрацией клана; 

- нарушает настоящие правила клана;

4.2 Если участница клана пропадает без предупреждения на срок более 7 дней, то она может быта исключена.

❺. Изменения или внесения в правила дополнений:

5.1 Правом изменения или внесения в поправок в правила обладает только администрация клана. Но! Участницы клана в праве предложить свои поправки или предложения.

❻. МЫ ПРОТИВ ВОЙНЫ! В нашем клане девчонки с разных стран. ВСЕ темы о политике неприемлемы.  За нарушение правила - исключение из клана. 

P.S. В чате мы много кого обсуждаем, и если вам неприятно это читать или же (не дай бог😂) в этих обсуждениях будут задействованы ваши друзья, то пишите об этом сразу в чат или же администрации) Не нужно сливать инфу с чата или же молчать, а потом выходить с клана из-за этого🥹 Лучше напишите нам и мы обсудим и решим все вопросики, чем в крысу сливать инфу🥺"""


# ===================== ПРЕДСКАЗАНИЯ (200 шт.) =====================
# 100 универсальных, 50 красоты, 50 мотивации — все с эмодзи в конце.
PREDICTIONS = [
    # 1–100: универсальные
    "Сегодня твой день — даже если облачно ☁️",
    "Улыбка решит больше, чем кажется 😊",
    "Делай по любви — и будет кайф 💖",
    "Вселенная сегодня на твоей стороне ✨",
    "Ты видишь больше, чем другие — доверься себе 👁️",
    "Маленький шаг тоже движение вперёд 👣",
    "То, что казалось сложным, окажется простым 🔓",
    "Кто-то сегодня мечтает о встрече с тобой 💌",
    "Ты — как утренний луч, тёплый и честный ☀️",
    "Бери то, что по праву твоё 🗝️",
    "Новая дружба рядом — будь открыта 🤝",
    "Не спеши — правильное не уйдёт 🕰️",
    "Лучшее решение — из спокойствия 🧘‍♀️",
    "Твоя доброта — твоя суперсила 🦸‍♀️",
    "Сегодня — день красивых совпадений 🧩",
    "Слухи остаются слухами — будь выше 🕊️",
    "Ты умеешь больше, чем привыкла думать 🧠",
    "Твоё сердце знает, куда идти ❤️",
    "Побалуй себя — ты это заслужила 🍰",
    "Стань тем человеком, кому самой приятно писать 💬",
    "Твоя энергия заразительна — в хорошем смысле ⚡️",
    "Скажи «да» маленькому приключению 🎒",
    "Смелость — это мягко и спокойно сказать «я могу» 🐚",
    "Пусть сегодня будет легко, как дыхание 🌬️",
    "Прими комплимент — он заслуженный 🌷",
    "Три глотка воды — и голова яснее 💧",
    "Сомнение — это просто туман, солнце уже встаёт 🌄",
    "Твоя интуиция — как Wi-Fi: невидима, но тянет 🔮",
    "Сделай добро и забудь — оно найдёт тебя 🌈",
    "Не сравнивай — у тебя своя траектория 🌌",
    "Нежность к себе — лучший план на день 🫶",
    "Пусть душа сегодня потанцует 💃",
    "Ты — чьё-то «повезло» 🍀",
    "Сделай паузу, ты не машина ⏸️",
    "Границы — это любовь к себе 🧱",
    "Ты не обязана быть удобной никому 👑",
    "Твоя искренность — золото 🪙",
    "Обернись: ты уже далеко прошла 🛤️",
    "Вселенная слышит шёпотом — говори мягко 🌙",
    "Письмо самой себе — лучшее лекарство ✍️",
    "Смех продлевает кайф от жизни 😂",
    "Найди маленькую красоту рядом и улыбнись 🌼",
    "Чудеса любят, когда в них верят ✨",
    "Сделай шаг без шума — результаты скажут сами 📈",
    "Будь там, где тепло к тебе 🔥",
    "Устаёшь — отдохни, не сдавайся 🛌",
    "Вокруг тебя больше поддержки, чем кажется 🤗",
    "Пусть в ленте будет меньше мусора и больше тебя 🧹",
    "Слова важны — выбирай нежные 🌸",
    "Ты — главный персонаж, не статист 🎬",
    "Разреши себе быть неидеальной и счастливой 🎈",
    "Твоя забота о других прекрасна — не забудь о себе 🫖",
    "Иногда «нет» — это лучший «да» себе 🚪",
    "Твой смех — твой фирменный парфюм 💐",
    "Выбери удобные кроссы и иди в кайф 👟",
    "Ты можешь медленно, но точно — это сила 🐢",
    "Слушай тело — оно мудрее календаря 🗓️",
    "Отключи лишние уведомления — включи себя 🔕",
    "Твои желания — не каприз, а направление 🧭",
    "Позволь чудесам случаться без плана 🎁",
    "Ты — мягкая мощь 🌊",
    "Сегодня будет повод сказать «вот это да!» 🤩",
    "Просто спроси — и двери откроются 🚪",
    "Ты — как хороший плейлист: и танцевать, и думать 🎧",
    "Чистая комната — чистая голова 🧼",
    "Не трать красоту на сомнения 💄",
    "Пусть будет вкусный кофе и спокойный день ☕️",
    "Самая важная встреча — с собой в зеркале 🪞",
    "Ты — причина, по которой кому-то легче дышится 💞",
    "Будь бережна к себе, как к любимой подруге 💌",
    "Отпусти то, что тянет вниз — и взлетишь 🎈",
    "Сегодня идеальный день для «с нуля» 🔁",
    "Ты умеешь радоваться мелочам — это редкость 🌟",
    "Сделай комплимент другой девочке — мир станет теплее 💬",
    "Уверенность — это тихо: «я справлюсь» 🤍",
    "Вдох — надежда, выдох — спокойствие 🌬️",
    "Ты прекрасна в процессе, не только в результате 🧩",
    "Спроси помощь — это смелость, а не слабость 🦋",
    "Выбери себя — и мир подстроится 💫",
    "Сегодня тебя ждёт приятная новость 🗞️",
    "Радуйся путём, не только финишем 🏁",
    "Оберегай свою мягкость — в ней сила 🐑",
    "Сердцу видно дальше, чем глазам ❤️",
    "То, что для тебя — тебя найдёт 📬",
    "Ты — как весна: не спрашиваешь, просто расцветаешь 🌷",
    "Мир не идеален — и это даёт шанс тебе 🌍",
    "Планы — хорошо, но ты важнее планов 🗺️",
    "Сегодня будет кому сказать «спасибо» 🙏",
    "Ты — редкая, это правда 💎",
    "Смени экран на небо на 5 минут — полегчает ☁️",
    "Скажи себе «молодец» — ты это услышишь 🥰",
    "Пусть будет тепло в душе и носках 🧦",
    "Твой свет видно даже сквозь тучи 🌥️",
    "Доброта к себе — не лень, а мудрость 🦉",
    "Будь в моменте: там жизнь 🫧",
    "Ты — украшение этого дня 🎀",
    "Сделай фото улыбки — пригодится 😁",
    "Пусть сегодня будет «легко» 🌿",
    "Ты прекрасна именно сейчас, без условий 🌼",
    "Твоя история — уже вдохновение для кого-то 📖",
    "Внутри тебя — дом, где спокойно 🏡",
    "Ты — лучший подарок самой себе 🎁",
    # 101–150: про красоту и самооценку
    "Ты красивая не вопреки, а потому что ты — ты 💖",
    "Твоя мимика — твоя магия ✨",
    "Без фильтров ты ещё нежнее 🌸",
    "Твои волосы сегодня слушаются тебя 😌",
    "Твои глазки — две маленькие галактики 🌌",
    "Помада — это просто вишенка, ты — торт 🍰",
    "Ты — как утро после дождя: чистая и свежая ☔️",
    "Твоя улыбка — мой любимый аксессуар 😍",
    "Красота — это твоё настроение, а оно супер 💃",
    "Сегодня тебе идёт всё, даже тапочки 🩴",
    "Ты светишься — и это не хайлайтер ✨",
    "Твой стиль — про тебя, а ты — про красоту 👜",
    "Самая модная вещь — твоя уверенность 👑",
    "Зеркало тебя обожает сегодня 🪞",
    "Твой профиль — произведение искусства 🖼️",
    "Ты — эстетика дня 🌷",
    "Твои ресницы машут удаче 👀",
    "У тебя идеальный сегодня вайб 🎧",
    "Ты — как тёплый свет лампы в уютной комнате 🕯️",
    "Ни у кого нет твоей улыбки — это роскошь 💎",
    "Красота — это добро, и у тебя его много 🤍",
    "Лицо отдыхает, а ты сияешь ✨",
    "Ты — лучший фильтр для себя 🫶",
    "Фото 0.5 тебя тоже любит 📸",
    "Твои движения — танец души 💞",
    "Твоя осанка — уверенность и мягкость 🧘‍♀️",
    "Красивее тебя только твоё сердце ❤️",
    "Твоя кожа говорит «спасибо» за заботу 🫧",
    "Ты — муза самой себя 🎨",
    "Твоя красота — в твоей нежности 🌿",
    "На тебе сегодня взгляд держится дольше обычного 👀",
    "Ты — стильная случайность Вселенной ✨",
    "Красота — это когда спокойно внутри 🌊",
    "Твой смех — самая красивая мелодия 🎶",
    "Ты — core всей этой эстетики 💗",
    "Легкий блеск в глазах — и весь мир лучше 💫",
    "Ты — это тренд, который не устареет 📈",
    "Сияй по расписанию: всегда 🌟",
    "Ты — топовая версия себя 🏆",
    "Твоя красота — не для сравнения, а для жизни 🌺",
    "Ты — как любимый свитер: уютно и тепло 🧶",
    "Максимально тебе идёт «быть собой» 💋",
    "У тебя свой почерк красивости ✍️",
    "Ты прекрасна без «но» и «если» 💖",
    "Ты — art без рамок 🖌️",
    "Ты — мой личный Pinterest 🌈",
    "Сегодня лайки — просто подтверждение очевидного ✅",
    "Твоя красота — это твоя свобода 🕊️",
    "Ты — нежный шторм, который хочется обнять 🌪️🤍",
    "Ты — как луч золотого часа ☀️",
    # 151–200: мотивация и действие
    "Сделай маленький шаг — он решающий 👣",
    "Лучший день начать — сегодня 📅",
    "Ты способна дисциплиной превратить мечту в план 🗂️",
    "Спроси себя: «что сделает меня счастливее?» и сделай это 🎯",
    "Гордилась бы собой? Тогда вперёд 💪",
    "Не нужно всё — нужно то, что важно тебе 🎯",
    "Пять минут сейчас лучше часа «потом» ⏱️",
    "Совершенство мешает старту — начинай как есть 🚀",
    "Сложно — это не «невозможно» 🧗‍♀️",
    "План + действие = магия 📈",
    "Неумение — это ещё не навсегда 📚",
    "Вдохновись, а потом сделай по-своему 💡",
    "Попроси помощи — ускоришь путь 🤝",
    "Сделай паузу, но не стоп ⏸️",
    "Люби процесс — и он полюбит тебя 🔁",
    "Меньше прокрутки, больше жизни 📵",
    "Привычки — твои маленькие помощники 🧩",
    "Ты — автор этой истории, пиши смелее ✍️",
    "Твоя дисциплина — форма любви к мечте 🫶",
    "Пусть будет по-твоему — ты старалась 💯",
    "Сомнение уходит после первого действия 🏃‍♀️",
    "Запусти таймер на 20 минут — и начни ⏳",
    "Не сравнивай путь — сравнивай усилия 💥",
    "Выдох — и сделай звонок/шаг/шажок 📞",
    "Твоя энергия заразительна — делись ею ⚡️",
    "Если страшно — значит важно 🌟",
    "Пусть вдохновит тебя твой завтрашний «спасибо» 💌",
    "Ты умеешь — просто ещё не пробовала так 💡",
    "Собери себя по кусочкам — и станцуй 💃",
    "Лучшее «потом» — это «сейчас» 🕒",
    "Делай как умеешь — и станет лучше 🧱",
    "Заметки — твой второй мозг 📓",
    "Смена обстановки — смена мысли 🌿",
    "Утро — для тебя, не для телефона 🌅",
    "Не жди мотивацию — стань ей 🔥",
    "Ты — причина, по которой это получится 🗝️",
    "Ставь тайные цели и громкие галочки ✅",
    "Тише едешь — дальше будешь 🐢",
    "Импульс важнее идеальности ⚡️",
    "Скажи «да» себе и делу 💬",
    "Капля за каплей — океан 🌊",
    "Сегодня ты ближе, чем вчера 🧭",
    "Результат — это повторение маленьких шагов 🔁",
    "Учись радоваться дисциплине, она про свободу 🕊️",
    "Сначала сделай, потом сомневайся 🛠️",
    "Убери лишнее — останется важное 🧹",
    "Двигайся красиво и по-своему 💃",
    "Ты — та, кто делает, а не только мечтает 💫",
    "Сделай именно столько, сколько можешь — этого достаточно 🤍",
]


# ===================== ТАРО (22 аркана) =====================
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
    ("Мир 🌍", "завершение, целостность, успех", "незавершённость, задержки"),
]


# ===================== РЕАКЦИИ =====================
HUGS_MESSAGES = [
    "Обнимаю тебя крепко-крепко 🫂 Всё будет хорошо!",
    "Тебя кто-то обнимает прямо сейчас 🤗 Надеюсь, тебе стало теплее!",
    "Мягкие обнимашки на твой день! 🧸 Ты супер!",
    "Вот так нежно и заботливо — обнимаю 💞",
    "Кто не обнимется — тот не играет в кастомке!",
    "🫂 Токсиков тоже иногда обнимают… по голове… табуреткой 🙃",
]

PIPISA_UP_REACTIONS = [
    "Пиписа выросла как на дрожжах! 🍆✨",
    "Ого! Такая прибавка, аж в чате тепло стало 😳",
    "Пиписа тянется к солнцу! ☀️",
    "Сегодня удачный день для роста! 📈",
]

PIPISA_DOWN_REACTIONS = [
    "Упс... что-то пошло не так 😬",
    "Пиписа сжалась от холода 🥶",
    "Грустный день, даже пиписа поникла 😢",
    "Ничего, завтра вырастет снова! 💪",
]


# ===================== ВСПОМОГАТЕЛЬНОЕ =====================
def html_code(s: str) -> str:
    # оборачиваем в моноширный блок <code>...</code>
    return f"<code>{s}</code>"


def user_display(user_id: int) -> str:
    u = state["users"].get(str(user_id))
    if not u:
        return f"юзер {user_id}"
    return u.get("name") or f"юзер {user_id}"


def ensure_user(user_id: int):
    suid = str(user_id)
    if suid not in state["users"]:
        state["users"][suid] = {
            "name": "",
            "nickname": "",
            "uid": "",
            "bday": "",
            "city": "",
            "social": "",
            "joined_date": "",
            "quote": "",
            "pipisa": 0.0,
            "last_pipisa": None,
            "last_prediction": None,
            "last_tarot": None,
            "married_to": None
        }


def today_str() -> str:
    return date.today().isoformat()


# ===================== ПРИВЕТСТВИЕ НОВЫХ =====================
async def greet_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cmu = update.chat_member
    if not cmu:
        return
    old = cmu.old_chat_member.status
    new = cmu.new_chat_member.status
    if (old in ("left", "kicked")) and (new in ("member", "administrator", "creator")):
        user = cmu.new_chat_member.user
        text = (
            f"Добро пожаловать, {user.mention_html()}❣️ "
            f"Ознакомься пожалуйста с правилами клана (https://telegra.ph/Pravila-klana-ঐOnlyGirlsঐ-05-29)🫶 "
            f"Важная информация всегда в закрепе❗️ Клановая приставка: ঔ"
        )
        await context.bot.send_message(chat_id=cmu.chat.id, text=text, parse_mode="HTML")


# ===================== /START и /ABOUT =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
        "/rules — правила клана\n"
        "/about — это меню"
    )


# ===================== /RULES =====================
async def rules(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(RULES_TEXT)


# ===================== ПРОФИЛЬ: /profile =====================
def render_profile(u: dict) -> str:
    name = u.get("name") or "не указано"
    nickname = u.get("nickname") or ""
    uid = u.get("uid") or ""
    bday = u.get("bday") or "не указано"
    city = u.get("city") or "не указан"
    social = u.get("social") or "не указано"
    joined = u.get("joined_date") or "не указано"
    quote = u.get("quote") or "—"
    pipisa = u.get("pipisa", 0.0)

    married_to = u.get("married_to")
    married_line = f"💍 В браке с {married_to}\n" if married_to else ""

    text = (
        f"🙋‍♀️ Имя: {name}\n"
        f"🎮 Ник в игре: {html_code(nickname)}\n"
        f"🔢 UID: {html_code(uid)}\n"
        f"🎂 Дата рождения: {bday}\n"
        f"🏙 Город: {city}\n"
        f"📲 ТТ или inst: {social}\n"
        f"📅 Дата вступления: {joined}\n"
        f"🍆 Пиписа: {pipisa:.1f} см\n"
        f"{married_line}"
        f"📝 Девиз: {quote}"
    )
    return text


async def profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    if uid not in state["users"]:
        await update.message.reply_text("Профиль не найден. Используй /editprofile чтобы создать 🌸")
        return
    text = render_profile(state["users"][uid])
    await update.message.reply_text(text, parse_mode="HTML")


# ===================== /editprofile (пошагово) =====================
(
    STEP_NAME,
    STEP_NICK,
    STEP_UID,
    STEP_BDAY,
    STEP_CITY,
    STEP_SOCIAL,
    STEP_JOINED,
    STEP_QUOTE
) = range(8)


async def editprofile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ensure_user(update.effective_user.id)
    context.user_data["profile_answers"] = {}
    await update.message.reply_text("Как тебя зовут? (имя)")
    return STEP_NAME


async def _save_and_next(update, context, key, next_step, question):
    text = update.message.text.strip()
    context.user_data["profile_answers"][key] = text
    await update.message.reply_text(question)
    return next_step


async def step_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Сохраняем кликабельное имя (mention)
    mention = update.effective_user.mention_html()
    context.user_data["profile_answers"]["name"] = mention
    await update.message.reply_text("Какой у тебя ник в игре?")
    return STEP_NICK


async def step_nick(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_and_next(update, context, "nickname", STEP_UID, "Какой у тебя UID?")


async def step_uid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_and_next(update, context, "uid", STEP_BDAY, "Когда у тебя день рождения? (например, 01.01.2000)")


async def step_bday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_and_next(update, context, "bday", STEP_CITY, "Из какого ты города?")


async def step_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_and_next(update, context, "city", STEP_SOCIAL, "Оставь ссылку на свой TikTok или Instagram:")


async def step_social(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_and_next(update, context, "social", STEP_JOINED, "Когда ты вступила в чат? (например, 01.08.2025)")


async def step_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return await _save_and_next(update, context, "joined_date", STEP_QUOTE, "Поделись своим девизом или любимой цитатой:")


async def step_quote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["profile_answers"]["quote"] = update.message.text.strip()
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)

    # Переносим ответы в глобальное хранилище
    saved = state["users"][uid]
    for k, v in context.user_data["profile_answers"].items():
        saved[k] = v
    # Пиписа и сервисные даты не трогаем
    save_state()
    await update.message.reply_text("Профиль обновлён ✅")
    return ConversationHandler.END


# ===================== /pipisa (1 раз в день) =====================
def _rand_delta():
    # от -10.0 до +10.0, исключая 0.0 (иначе всегда скучно)
    d = round(random.uniform(-10.0, 10.0), 1)
    if d == 0.0:
        d = 0.1 if random.random() > 0.5 else -0.1
    return d


async def pipisa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]

    last = u.get("last_pipisa")
    if last == today_str():
        await update.message.reply_text("Пипису можно растить/мерить только раз в день! 🌱")
        return

    delta = _rand_delta()
    new_val = round(float(u.get("pipisa", 0.0)) + delta, 1)
    if new_val < 0:
        new_val = 0.0

    u["pipisa"] = new_val
    u["last_pipisa"] = today_str()
    save_state()

    reaction = random.choice(PIPISA_UP_REACTIONS if delta > 0 else PIPISA_DOWN_REACTIONS)
    await update.message.reply_text(
        f"Изменение: {delta:+.1f} см\nТекущий размер: {new_val:.1f} см\n{reaction}"
    )


# ===================== РЕЙТИНГИ: /top5 и /rating =====================
async def top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)[:5]
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще 🌱")
        return
    text = "🏆 ТОП-5 пипис клана:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or uid}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")


async def rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rows = sorted(state["users"].items(), key=lambda kv: kv[1].get("pipisa", 0.0), reverse=True)
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще 🌱")
        return
    text = "📊 Полный рейтинг пипис:\n"
    for i, (uid, u) in enumerate(rows, 1):
        text += f"{i}. {u.get('name') or uid}: {u.get('pipisa', 0.0):.1f} см\n"
    await update.message.reply_text(text, parse_mode="HTML")


# ===================== /predskaz (1 раз в день) =====================
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


# ===================== /tarot (1 раз в день) =====================
async def tarot(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    u = state["users"][uid]

    if u.get("last_tarot") == today_str():
        await update.message.reply_text("🃏 Расклад Таро доступен раз в день!")
        return

    card, upright, reversed_m = random.choice(TAROT_CARDS)
    is_reversed = random.choice([True, False])
    meaning = reversed_m if is_reversed else upright
    u["last_tarot"] = today_str()
    save_state()
    await update.message.reply_text(
        f"<b>{card}</b> — {meaning}",
        parse_mode="HTML"
    )


# ===================== /hugs =====================
async def hugs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Если указан @user — обнимаем его, иначе — рандом или всех
    if context.args:
        target = context.args[0]
        await update.message.reply_text(f"🤗 {update.effective_user.mention_html()} обняла {target}!", parse_mode="HTML")
        return

    # Попробуем рандомно выбрать кого-то из зарегистрированных
    pool = [int(uid) for uid in state["users"].keys() if int(uid) != update.effective_user.id]
    if pool:
        target_id = random.choice(pool)
        await update.message.reply_text(
            f"🤗 {update.effective_user.mention_html()} обняла {user_display(target_id)}!",
            parse_mode="HTML"
        )
    else:
        await update.message.reply_text(random.choice(HUGS_MESSAGES))


# ===================== /lesbi (1 раз в день) =====================
async def lesbi(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # нужна минимум пара профилей
    pool = [int(uid) for uid, u in state["users"].items() if u.get("name")]
    if len(pool) < 2:
        await update.message.reply_text("Недостаточно участниц для пары")
        return

    if state["last_lesbi_date"] == today_str():
        pair = state.get("last_lesbi_pair")
        if pair:
            a, b = pair
            await update.message.reply_text(
                f"👭 Пара дня уже выбрана: {user_display(a)} + {user_display(b)} 💞",
                parse_mode="HTML"
            )
            return
        # если почему-то пары нет, продолжаем и выбираем

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
    msg = random.choice(lines).format(a=user_display(a), b=user_display(b))
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")


# ===================== СВАДЬБЫ =====================
# /love @user — делает предложение
# /acceptlove — принять
# /declinelove — отклонить
# /divorce — запрос развода (нужно подтверждение партнёра /acceptdivorce)

async def love(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Укажи, кому предложение: /love @username")
        return
    target_username = context.args[0].lstrip("@")
    # найдём user_id по профилям (по name упоминание не всегда содержит username — сохранённого может не быть)
    # примем решение: предложить любому, у кого в имени есть этот юзернейм
    target_id = None
    for uid, u in state["users"].items():
        # имя хранится в виде mention_html, username может быть неявен, поэтому просто пробуем по uid
        if u.get("name") and target_username in u.get("name"):
            target_id = int(uid)
            break

    if not target_id:
        await update.message.reply_text("Не нашла участницу с таким username в профилях. Попроси её сначала сделать /editprofile.")
        return

    proposer = update.effective_user.id
    ensure_user(proposer)
    ensure_user(target_id)

    # Проверка: не в браке ли уже?
    if state["users"][str(proposer)].get("married_to"):
        await update.message.reply_text("Ты уже в браке 💍")
        return
    if state["users"][str(target_id)].get("married_to"):
        await update.message.reply_text("Участница уже в браке 💍")
        return

    # Создаём запрос
    state["proposals"][str(target_id)] = proposer
    save_state()
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"💍 {update.effective_user.mention_html()} сделала предложение @{target_username}! "
             f"Ответ — команда /acceptlove или /declinelove",
        parse_mode="HTML"
    )


async def acceptlove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = str(update.effective_user.id)
    if target_id not in state["proposals"]:
        await update.message.reply_text("Нет активного предложения для тебя.")
        return
    proposer = state["proposals"].pop(target_id)
    ensure_user(proposer)
    ensure_user(int(target_id))

    # Обновим статусы брака
    pa = state["users"][str(proposer)]
    pb = state["users"][target_id]
    pa["married_to"] = user_display(int(target_id))
    pb["married_to"] = user_display(proposer)
    save_state()

    lines = [
        "💍 {a} и {b} теперь официально жена и жена! Поздравляем! 🎉",
        "👰‍♀️👰‍♀️ Сыграли свадьбу: {a} + {b} = 💒 Любовь!",
        "🥂 Появилась новая семейная пара: {a} & {b}! Пусть будет счастье! 🫶",
        "🎊 {a} и {b} теперь супруги в нашем клане! Нежности и обнимашек! 🥰",
    ]
    msg = random.choice(lines).format(a=user_display(proposer), b=user_display(int(target_id)))
    await context.bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")


async def declinelove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_id = str(update.effective_user.id)
    if target_id not in state["proposals"]:
        await update.message.reply_text("Нет активного предложения для тебя.")
        return
    state["proposals"].pop(target_id)
    save_state()
    await update.message.reply_text("Предложение отклонено.")


async def divorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = str(update.effective_user.id)
    ensure_user(update.effective_user.id)
    me = state["users"][uid]
    if not me.get("married_to"):
        await update.message.reply_text("Ты не в браке.")
        return

    # Найдём партнёра по имени (сохраняется как текст)
    partner_id = None
    for pid, u in state["users"].items():
        if u.get("name") and me["married_to"] == u.get("name"):
            partner_id = int(pid)
            break
    if not partner_id:
        await update.message.reply_text("Не нашла партнёрку в базе. Обратитесь к админам.")
        return

    state["divorce_requests"][str(partner_id)] = int(uid)
    save_state()
    await update.message.reply_text("Запрос на развод отправлен. Партнёрке нужно выполнить /acceptdivorce.")


async def acceptdivorce(update: Update, context: ContextTypes.DEFAULT_TYPE):
    me = str(update.effective_user.id)
    if me not in state["divorce_requests"]:
        await update.message.reply_text("Нет активного запроса на развод.")
        return
    other = state["divorce_requests"].pop(me)
    # Сброс брака у обеих
    if str(other) in state["users"]:
        state["users"][str(other)]["married_to"] = None
    if me in state["users"]:
        state["users"][me]["married_to"] = None
    save_state()
    await context.bot.send_message(
        chat_id=CHAT_ID,
        text=f"💔 Развод! {user_display(other)} и {user_display(int(me))} расстались.",
        parse_mode="HTML"
    )


# ===================== /predskaz АЛЬЯС =====================
async def prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # на случай, если кто-то будет звать /prediction
    await predskaz(update, context)


# ===================== РЕГИСТРАЦИЯ ХЕНДЛЕРОВ =====================
def build_application():
    app = ApplicationBuilder().token(TOKEN).build()

    # Приветствия новых
    app.add_handler(ChatMemberHandler(greet_new_member, ChatMemberHandler.CHAT_MEMBER))

    # Профиль
    edit_conv = ConversationHandler(
        entry_points=[CommandHandler("editprofile", editprofile)],
        states={
            STEP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_name)],
            STEP_NICK: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_nick)],
            STEP_UID: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_uid)],
            STEP_BDAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_bday)],
            STEP_CITY: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_city)],
            STEP_SOCIAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_social)],
            STEP_JOINED: [MessageHandler(filters.TEXT & ~filters.COMMAND, step_joined)],
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
    app.add_handler(CommandHandler("prediction", prediction))  # алиас
    app.add_handler(CommandHandler("tarot", tarot))

    # Свадьбы/разводы
    app.add_handler(CommandHandler("love", love))
    app.add_handler(CommandHandler("acceptlove", acceptlove))
    app.add_handler(CommandHandler("declinelove", declinelove))
    app.add_handler(CommandHandler("divorce", divorce))
    app.add_handler(CommandHandler("acceptdivorce", acceptdivorce))

    return app


# ===================== ЗАПУСК =====================
if __name__ == "__main__":
    application = build_application()
    print("OnlyGirls bot запущен…")
    application.run_polling(close_loop=False)
