from telegram import *

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
)

import logging
import subprocess
from gpiozero import CPUTemperature
from time import sleep
import redis

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# setting some constants - particularly chat id, so it only sends messages to me (hopefully!)
THRESHOLD_TEMP = 60
CHAT_ID = ***REMOVED***

r = redis.Redis()


# basic start function - creates the keyboard ect
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [['Check Temperature']]
    menu_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text('Hello!', reply_markup=menu_markup)


# called very minute using the run_repeating job queue function - makes sure it isn't too hot
# to add inline button to reboot if over 60
async def autoCheckTemp(context: CallbackContext) -> None:
    currentTemp = CPUTemperature().temperature
    if currentTemp > THRESHOLD_TEMP:
        await context.bot.send_message(text=f'THRESHOLD TEMP EXCEEDED AT {currentTemp}°C', chat_id=CHAT_ID)


# allows me to reboot the bot
# add a handler - possibly inline and command handled
# need to create the script
async def reboot(update: Update, context: CallbackContext) -> None:
    message_id = (await context.bot.send_message(text='Rebooting...', chat_id=CHAT_ID))["message_id"]
    r.sadd('reboot_message', message_id)
    sleep(5)
    subprocess.run(['sh', '/home/pi/Scripts/rebooter.sh'])


# allows manual checking of cpu temperature
async def checkTemp(update: Update, context: CallbackContext) -> None:
    currentTemp = CPUTemperature().temperature
    await context.bot.send_message(text=f'Current Temperature: {currentTemp}°C', chat_id=CHAT_ID)


# in case an unrecognized message is sent
async def unknownCommand(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Unknown command')


async def awakened(context: CallbackContext) -> None:
    try:
        message_id = str(r.spop('reboot_message', 1)[0]).replace('b', '').replace("'", "")
        await context.bot.edit_message_text(message_id=int(message_id), chat_id=CHAT_ID,
                                            text='Successfully rebooted!')
    except:
        await context.bot.send_message(text='The pi is awake!', chat_id=CHAT_ID)
    # to add it editing the previous message - temporarily store message id in redis ? replace each ime


def main() -> None:
    # create the bot
    application = Application.builder().token(***REMOVED***).build()

    # allows me to edit the job queue - ie tell the bot when to call a function
    job_queue = application.job_queue

    initial_job = job_queue.run_once(awakened, 0)
    job_minute = job_queue.run_repeating(autoCheckTemp, interval=60, first=10)

    # a few handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('reboot', reboot))
    application.add_handler(MessageHandler(filters.Regex('Check Temperature'), checkTemp))
    application.add_handler(MessageHandler(filters.ALL, unknownCommand))

    # runs the bot
    application.run_polling()


# runs main function
if __name__ == '__main__':
    main()
