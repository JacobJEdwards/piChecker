# †ø∂ø
# Finish command line
# i am not sure what else whatever i can think of...

from telegram import *

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    CallbackContext,
    ContextTypes,
    CallbackQueryHandler,
)

from functools import wraps
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


# function to define who can use certain commands
def restricted(func):
    @wraps(func)
    async def wrapped(update, context, *args, **kwargs):
        user_id = update.effective_user.id
        if user_id != CHAT_ID:
            await context.bot.send_message(text=f"Unauthorized access denied for {user_id}.", chat_id=CHAT_ID)
            return
        return await func(update, context, *args, **kwargs)
    return wrapped


# basic start function - creates the keyboard ect
async def start(update: Update, context: CallbackContext) -> None:
    keyboard = [['Check Temperature'],['Memory Info']]
    menu_markup = ReplyKeyboardMarkup(keyboard)
    await update.message.reply_text('Hello!!!', reply_markup=menu_markup)


# called very minute using the run_repeating job queue function - makes sure it isn't too hot
async def autoCheckTemp(context: CallbackContext) -> None:
    currentTemp = CPUTemperature().temperature
    if currentTemp > THRESHOLD_TEMP:
        inlineKeyboard = [
            [InlineKeyboardButton('Reboot', callback_data='1')],
            [InlineKeyboardButton('Do nothing', callback_data='2')]
        ]
        reply_markup = InlineKeyboardMarkup(inlineKeyboard)
        await context.bot.send_message(text=f'THRESHOLD TEMP EXCEEDED AT {currentTemp}°C',
                                       chat_id=CHAT_ID, reply_markup=reply_markup)


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    print(query.data)
    await query.answer()
    if query.data == '1':
        await query.edit_message_text(text="Starting reboot")
        await reboot(update, context)
    else:
        await query.edit_message_text(text='OK')


# allows me to reboot the bot
# add a handler - possibly inline and command handled
# need to create the script
@restricted
async def reboot(update: Update, context: CallbackContext) -> None:
    message_id = (await context.bot.send_message(text='Rebooting...', chat_id=CHAT_ID))["message_id"]
    r.sadd('reboot_message', message_id)
    sleep(5)
    subprocess.run(['sh', '/home/pi/Scripts/rebooter.sh'])


# allows manual checking of cpu temperature
async def checkTemp(update: Update, context: CallbackContext) -> None:
    currentTemp = CPUTemperature().temperature
    await context.bot.send_message(text=f'Current Temperature: {currentTemp}°C', chat_id=CHAT_ID)

async def memInfo(update: Update, context: CallbackContext) -> None:
    output = subprocess.run(['sh', '/home/pi/Scripts/memoryInfo.sh'], capture_output=True).stdout.decode()
    await context.bot.send_message(text=output, chat_id=CHAT_ID)


# in case an unrecognized message is sent
async def unknownCommand(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text('Unknown command')


# calls this as soon as the pi turns on using job queue
async def awakened(context: CallbackContext) -> None:
    message_id = r.spop('reboot_message', 1)[0].decode()
    await context.bot.edit_message_text(message_id=int(message_id), chat_id=CHAT_ID,
                                            text='Successfully rebooted!')

    await context.bot.send_message(text='The pi is awake!', chat_id=CHAT_ID)


@restricted
async def commandLine(update: Update, context: CallbackContext) -> None:
    commandArray = context.args
    commandString = ' '.join(commandArray)
    output = subprocess.run(commandString, capture_output=True, shell=True).stdout.decode('UTF-8')
    await context.bot.send_message(text=output, chat_id=CHAT_ID)


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
    application.add_handler(CommandHandler('meminfo', memInfo))
    application.add_handler(CommandHandler('run', commandLine))

    application.add_handler(MessageHandler(filters.Regex('Memory Info'), memInfo))
    application.add_handler(MessageHandler(filters.Regex('Check Temperature'), checkTemp))

    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.ALL, unknownCommand))

    # runs the bot
    application.run_polling()


# runs main function
if __name__ == '__main__':
    main()
