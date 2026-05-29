from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from langchain_core.messages import HumanMessage
from telegram.ext import CommandHandler
import asyncio

from app.config import settings

# graph will be injected after build
graph = None

def set_graph(g):
    global graph
    graph = g

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)  # telegram user id as user_id
    msg = update.message.text

    await update.message.chat.send_action("typing")

    try:
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content=msg)],
                "user_id": user_id
            },
            config={
                "configurable": {
                    "thread_id": user_id,
                    "user_id": user_id
                },
                "recursion_limit": 10
            }
        )
        response = result["messages"][-1].content
    except Exception as e:
        error_str = str(e)
        print(f"[ERROR] Telegram handler failed for user {user_id}: {error_str}")

        if "tool call validation failed" in error_str:
            response = "I couldn't understand that amount. Could you rephrase? (e.g. 'I spent 200 on food')"
        elif "rate_limit_exceeded" in error_str:
            response = "I'm a bit overwhelmed right now. Please try again in a minute."
        else:
            response = "Sorry, something went wrong. Please try again."

    await update.message.reply_text(response)


async def summary_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    await update.message.chat.send_action("typing")

    try:
    
        result = await graph.ainvoke(
            {
                "messages": [HumanMessage(content="analyze my spending and give me a full financial health report with recommendations")],
                "user_id": user_id
            },
            config={
                "configurable": {
                    "thread_id": f"{user_id}_summary",
                    "user_id": user_id
                },
                "recursion_limit": 10
            }
        )
        response = result["messages"][-1].content

    except Exception as e:
        response = f"Something went wrong: {str(e)}"
    await update.message.reply_text(response)


def build_telegram_app(g):
    set_graph(g)
    app = ApplicationBuilder().token(settings.TELEGRAM_TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CommandHandler("summary", summary_command))  # 👈
    return app