from telegram import *

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    CallbackQueryHandler,
    ContextTypes,
    PreCheckoutQueryHandler
)

CHAT_ID =
USER_ID =

def start(update: Update, context: CallbackContext) -> None:
    print(update.effective_user.id)
    print(update.effective_chat.id)
def checkTemp(update: Update, context: CallbackContext) -> None:


def main() -> None:
    application = Application.builder().token(***REMOVED***).build()

    application.add_handler(CommandHandler('start', start))
