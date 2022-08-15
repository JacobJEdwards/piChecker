
import logging

from telegram import Update

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

from gpiozero import CPUTemperature


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


THRESHOLD_TEMP = 60
CHAT_ID = ***REMOVED***


async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [['Check Temperature']]
    menu_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text('Hello!', reply_markup=menu_markup)


async def autoCheckTemp(context: CallbackContext) -> None:
    currentTemp = CPUTemperature().temperature
    if currentTemp > THRESHOLD_TEMP:
        await context.bot.send_message(text=f'THRESHOLD TEMP EXCEEDED AT {currentTemp}°C', chat_id=CHAT_ID)


async def checkTemp(update: Update, context: CallbackContext) -> None:
    currentTemp = CPUTemperature().temperature
    await context.bot.send_message(text=f'Current Temperature: {currentTemp}°C', chat_id=CHAT_ID)


async def unknownCommand(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Unknown command')


def main() -> None:
    application = Application.builder().token(***REMOVED***).build()

    job_queue = application.job_queue
    job_minute = job_queue.run_repeating(autoCheckTemp, interval=60, first=10)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(MessageHandler(filters.Regex('Check Temperature'), checkTemp))
    application.add_handler(MessageHandler(filters.ALL, unknownCommand))

    application.run_polling()


if __name__ == '__main__':
    main()
