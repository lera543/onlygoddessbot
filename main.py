
import logging
import sqlite3
from datetime import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    ChatMemberHandler, ContextTypes, filters
)
from config import TOKEN

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    first_name TEXT,
    joined_date TEXT,
    bday TEXT,
    nickname TEXT,
    messages INTEGER DEFAULT 0,
    karma INTEGER DEFAULT 0,
    pp_size REAL DEFAULT 0,
    last_grow_date TEXT
)
""")
conn.commit()

BAD_WORDS = ["путин", "украина", "россия", "война", "кремль", "мобилизация", "политика", "навальный"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"Добро пожаловать, {user.first_name}! 🌙\n"
        "Я — Мать Богинь. Напиши /setprofile и вступи в магический круг ✨"
    )

async def prediction(update: Update, context: ContextTypes.DEFAULT_TYPE):
    import random
    predictions = [
        "Сегодня ты очаруешь всех 🌟",
        "Кто-то из клана смотрит на тебя с интересом 👀",
        "Твоя пиписа излучает магию 🍆✨",
        "Завари чай, будет странный день 🍵",
        "Обними кого-нибудь — и получишь +1 к любви 💘",
    ]
    await update.message.reply_text(random.choice(predictions))

async def set_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = user.username or ""
    first_name = user.first_name or ""
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    if cursor.fetchone():
        await update.message.reply_text("Профиль уже создан. Используй /myprofile ✨")
        return
    joined = datetime.now().strftime("%Y-%m-%d")
    cursor.execute("INSERT INTO users (user_id, username, first_name, joined_date) VALUES (?, ?, ?, ?)",
                   (user_id, username, first_name, joined))
    conn.commit()
    await update.message.reply_text("Профиль создан! 💖 Напиши /grow чтобы начать путь пиписы.")

async def my_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT * FROM users WHERE user_id=?", (user.id,))
    data = cursor.fetchone()
    if not data:
        await update.message.reply_text("Ты ещё не создала профиль. Напиши /setprofile 🌙")
        return
    _, username, name, joined, bday, nickname, msgs, karma, pp, _ = data
    days_in = (datetime.now() - datetime.strptime(joined, "%Y-%m-%d")).days
    text = (
        f"🌸 Профиль {name} (@{username})\n"
        f"🔹 Ник: {nickname or 'не указан'}\n"
        f"🎂 ДР: {bday or 'не указан'}\n"
        f"📆 В чате: {days_in} дней\n"
        f"💬 Сообщений: {msgs}\n"
        f"💖 Карма: {karma}\n"
        f"🍆 Пиписа: {pp:.1f} см"
    )
    await update.message.reply_text(text)

async def grow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT pp_size, last_grow_date FROM users WHERE user_id=?", (user.id,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text("Сначала создай профиль: /setprofile")
        return
    pp_size, last_grow = row
    today = datetime.now().date()
    if last_grow == str(today):
        await update.message.reply_text("Ты уже полила свою пипису сегодня 🌱")
        return
    import random
    growth = round(random.uniform(0.1, 2.5), 1)
    new_size = round(pp_size + growth, 1)
    cursor.execute("UPDATE users SET pp_size=?, last_grow_date=? WHERE user_id=?", (new_size, str(today), user.id))
    conn.commit()
    await update.message.reply_text(f"Твоя пиписа выросла на {growth} см и теперь {new_size} см 🍆✨")

async def size(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    cursor.execute("SELECT pp_size FROM users WHERE user_id=?", (user.id,))
    row = cursor.fetchone()
    if not row:
        await update.message.reply_text("Создай профиль: /setprofile")
        return
    await update.message.reply_text(f"Твоя текущая пиписа — {row[0]:.1f} см 🍆")

async def ranking(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cursor.execute("SELECT first_name, pp_size FROM users ORDER BY pp_size DESC LIMIT 5")
    rows = cursor.fetchall()
    if not rows:
        await update.message.reply_text("Рейтинг пуст. Поливай пипису чаще 🌱")
        return
    text = "🍆 Топ пипис клана:\n"
    for i, (name, size) in enumerate(rows, 1):
        text += f"{i}. {name}: {size:.1f} см\n"
    await update.message.reply_text(text)

async def anti_politics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message.text.lower()
    if any(word in msg for word in BAD_WORDS):
        await update.message.delete()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="⚠️ Магия ослабевает от слов о политике. Чат замедлен.",
        )
        await context.bot.set_chat_slow_mode_delay(update.effective_chat.id, 60)

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = update.chat_member.new_chat_member
    if member.status == "member":
        name = member.user.first_name
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🌸 Добро пожаловать, {name}! Напиши /setprofile и пусть магия начнётся ✨"
        )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("prediction", prediction))
    app.add_handler(CommandHandler("setprofile", set_profile))
    app.add_handler(CommandHandler("myprofile", my_profile))
    app.add_handler(CommandHandler("grow", grow))
    app.add_handler(CommandHandler("size", size))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(ChatMemberHandler(welcome, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, anti_politics))
    app.run_polling()

if __name__ == "__main__":
    main()
