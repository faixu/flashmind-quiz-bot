import os
import logging
from dotenv import load_dotenv
from telegram import Update, Poll
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    PollAnswerHandler,
    ContextTypes,
)

# Load secrets from .env
load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not TOKEN:
    raise ValueError("TELEGRAM_BOT_TOKEN is not set in environment variables!")

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

# Question Bank
QUESTIONS = [
    {
        "question": "Which gas is most abundant in Earth's atmosphere?",
        "options": ["Oxygen", "Nitrogen", "Carbon Dioxide", "Argon"],
        "correct_option_id": 1,
        "explanation": "Nitrogen makes up approximately 78% of Earth's atmosphere.",
    },
    {
        "question": "Which organ in the human body is primarily responsible for filtering blood?",
        "options": ["Heart", "Lungs", "Kidneys", "Liver"],
        "correct_option_id": 2,
        "explanation": "Kidneys filter waste materials and extra fluids from your blood.",
    },
    {
        "question": "What is the primary driver of ocean surface currents?",
        "options": ["Tectonic shifts", "Wind patterns", "Salinity gradients", "Underwater earthquakes"],
        "correct_option_id": 1,
        "explanation": "Global wind patterns drive the large-scale circulation of ocean surface waters.",
    },
]

# Track per-user active sessions
user_sessions = {}


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point when a user runs /start or /quiz."""
    chat_id = update.effective_chat.id
    user_sessions[chat_id] = {
        "score": 0,
        "current_index": 0,
    }

    await context.bot.send_message(
        chat_id=chat_id,
        text="🧠 **Welcome to FlashMind Quiz Bot!**\n\nSharpen your concepts with rapid interactive MCQs. Let's begin!",
        parse_mode="Markdown",
    )
    await send_quiz_poll(chat_id, context)


async def send_quiz_poll(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    """Sends the next native Telegram quiz poll."""
    session = user_sessions.get(chat_id)
    if not session:
        return

    index = session["current_index"]

    if index < len(QUESTIONS):
        q = QUESTIONS[index]
        await context.bot.send_poll(
            chat_id=chat_id,
            question=f"Q{index + 1}: {q['question']}",
            options=q["options"],
            type=Poll.QUIZ,
            correct_option_id=q["correct_option_id"],
            is_anonymous=False,
            explanation=q["explanation"],
            explanation_parse_mode="Markdown",
        )
    else:
        score = session["score"]
        total = len(QUESTIONS)
        pct = round((score / total) * 100, 1)

        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"🏁 **Quiz Completed!**\n\n"
                f"🎯 **Score:** `{score}/{total}` ({pct}%)\n\n"
                f"Send `/quiz` or `/start` to start a new practice round."
            ),
            parse_mode="Markdown",
        )
        del user_sessions[chat_id]


async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles option selection from the user."""
    answer = update.poll_answer
    user_id = answer.user.id

    if user_id in user_sessions:
        session = user_sessions[user_id]
        current_q = QUESTIONS[session["current_index"]]

        if answer.option_ids and answer.option_ids[0] == current_q["correct_option_id"]:
            session["score"] += 1

        session["current_index"] += 1
        await send_quiz_poll(user_id, context)


if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler(["start", "quiz"], start))
    app.add_handler(PollAnswerHandler(handle_answer))

    print("FlashMindQuizBot is running locally...")
    app.run_polling()