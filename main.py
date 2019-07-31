from telegram.ext import Updater, CommandHandler, Filters
from telegram.ext import CallbackQueryHandler, MessageHandler, ConversationHandler, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from odata1cw.core import Infobase

import requests
import json
import logging
import sys

# # main bot library
# from botlib import dms_test, getVehicles, menu_actions, locations, inv, error, login

# from compliance import handler as compliance_handler

'''
Command description for @BotFather

locations - stock balance
compliance - Sending and receiving from/to compliance 
login - registration in the system
inv - location inventory

'''

def hello(bot, update):
    update.message.reply_text('Hello {}'.format(
        update.message.from_user.first_name))


def start(bot, update):
    update.message.reply_text('Hello {}'.format(
        update.message.from_user.first_name))
    update.message.reply_text('''
1) Just type the tail of a vehicle's chassis.
2) /inv - cars, placed at specified Location
3) /locations - Locations summury 
4) /login - To ask permissions. Need once.

Type /start any time to show this help.
    ''')


def main():
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                        level=logging.INFO)

    if(len(sys.argv) != 2):
        updater = Updater('802189751:AAEhZZ8bZ59nb0BxZNzbFOlTyHiN82PbUAg')  

    elif(sys.argv[1] == 'DEBUG'):
        updater = Updater(
            '730634879:AAFnp_yIKcM4eCXFy75XcLSo9IoAWQaFYPU',
            #request_kwargs={'proxy_url': 'https://54.39.138.146:3128'})
            request_kwargs={'proxy_url': 'https://51.79.31.19:8080'})
    elif (sys.argv[1] == 'PROD'):
        updater = Updater('802189751:AAEhZZ8bZ59nb0BxZNzbFOlTyHiN82PbUAg')
    elif (sys.argv[1] == 'TEST'):
        updater = Updater('838750238:AAGysoEUeOL1MHM63pkXJn8Jp7V-g39rkM4')    
    else:
        print('Select DEBUG or PROD or TEST arg')
        return

    dp = updater.dispatcher
    # TODO need double check about InfoRegisters DMS Statuses
    # dp.add_handler(compliance_handler())
    dp.add_handler(CommandHandler('hello', hello))
    # dp.add_handler(CommandHandler('inv', inv,pass_user_data=True))
    dp.add_handler(CommandHandler('start', start))
    # dp.add_handler(CommandHandler('dms_test', dms_test,pass_user_data=True))
    # dp.add_handler(CommandHandler('locations', locations,pass_user_data=True))
    # dp.add_handler(CommandHandler('login', login,pass_user_data=True))
    # dp.add_handler(MessageHandler(Filters.text, getVehicles,pass_user_data=True))
    # dp.add_handler(CallbackQueryHandler(menu_actions, pass_user_data=True))
    # dp.add_error_handler(error)
    print(sys.version)
    print('''Start polling ()...'.format(sys.argv[1])''')
    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
