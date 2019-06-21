from telegram.ext import Updater, CommandHandler, Filters
from telegram.ext import CallbackQueryHandler, MessageHandler, ConversationHandler, RegexHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import ParseMode
from config import DMSConfig as cfg
import requests
import logging
import json
from dmsapi import checkLogin

logger = logging.getLogger(__name__)


def login(bot, update):
    u = update.message.from_user
    param = json.dumps({
        'id': u.id,
        'first_name': u.first_name,
        'last_name': u.last_name,
        'username': u.username,
    })
    r = requests.get(cfg.DMS_URL.format(
        'TelegramLogin', param), auth=cfg.DMS_AUTH)
    if(r.status_code != 200):
        logger.error('Update "{}" caused error "{}" ({})'.format(
            bot, r.status_code, 'TelegramLogin'))

    update.message.reply_text('''Well done {}. 
        Please wait for approval or contact 
        @Belov_Ilia  
        belov.penrose@gmail.com'''.format(
        u.first_name), parse_mode=ParseMode.HTML)


def error(bot, context, *args, **kwargs):
    print(args)
    print(kwargs)
    try:
        err = context.error
    except:
        err = context
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', bot, err)


def dms_test(bot, update):
    if(not checkLogin(update.message.from_user, update)):
        return

    update.message.reply_text('DMS')
    param = update.message.text
    r = requests.get(cfg.DMS_URL.format('test', param[10:]), auth=cfg.DMS_AUTH)
    update.message.reply_text(r.text)


def getVehicles(bot, update):
    if(not checkLogin(update.message.from_user, update)):
        return
    param = update.message.text
    r = requests.get(cfg.DMS_URL.format(
        'GetVehicles', param), auth=cfg.DMS_AUTH)

    if(r.status_code != 200):
        logger.error('Update "{}" caused error "{}" ({})'.format(
            bot, r.status_code, 'GetVehicles'))
        return False

    response = json.loads(r.text)
    msg = []

    if(len(response) == 0):
        msg.append({'text': 'No matches found', 'btn': False})
    else:
        for v in response[:5]:
            text = '{} {} {} {} [{}]\n{} ({}, {})'.format(
                v['Make'], v['Model'], v['YearVehicle'], v['Variant'], v['ChassisNo'],
                v['Status'], v['Location'], v['StatusDMS'])
            locations_btns = vehicleKeyboard(v['DMSID'], 'loc')
            btn = InlineKeyboardMarkup([locations_btns])
            msg.append({'text': text, 'btn': btn})

    for m in msg:
        update.message.reply_text(m['text'], reply_markup=m['btn'])

    if(len(response) > 1):
        update.message.reply_text('Founded {} vehicles'.format(len(response)))


def menu_actions(bot, update):
    query = update.callback_query
    vehicleCode = query.data.split('/')[0]
    action = query.data.split('/')[1]
    locationCode = query.data.split('/')[2]

    if(action == 'loc'):
        locationDescription = query.data.split('/')[3]
        param = json.dumps({'locationCode': locationCode,
                            'vehicleCode': vehicleCode,
                            'telegramUser': update.callback_query.message.chat.id})
        print(param)
        r = requests.get(cfg.DMS_URL.format(
            'SetVehicleLocation', param), auth=cfg.DMS_AUTH)
        bot.answer_callback_query(
            query.id, text='Result:{}'.format(r.text), show_alert=True)
        query.message.edit_text(
            query.message.text + '\nNew location: ' + locationDescription)  # Replace message
    elif(action == 'inv'):
        locationDescription = query.data.split('/')[3]
        r = requests.get(cfg.DMS_URL.format(
            'GetVehiclesByLocation', locationCode), auth=cfg.DMS_AUTH)
        response = json.loads(r.text)
        for v in response[:100]:
            text = '{} {} {} {} [{}]\n{} ({}, {})'.format(
                v['Make'], v['Model'], v['YearVehicle'], v['Variant'], v['ChassisNo'],
                v['Status'], v['Location'], v['StatusDMS'])
            query.message.reply_text(text)

        query.message.edit_text('At {} {} cars'.format(
            locationDescription, len(response)))  # Replace message


def inv(bot, update):
    if(not checkLogin(update.message.from_user, update)):
        return
    r = requests.get(cfg.ODATA_URL.format(
        'Catalog_PhysicalLocations'), auth=cfg.DMS_AUTH)
    if(r.status_code != 200):
        logger.error('Update "{}" caused error "{}" ({})'.format(
            bot, r.status_code, 'Catalog_PhysicalLocations'))
        return False
    locations_btns = vehicleKeyboard('', 'inv')
    btn = InlineKeyboardMarkup([locations_btns])
    update.message.reply_text('Select location', reply_markup=btn)


def locations(bot, update):
    if(not checkLogin(update.message.from_user, update)):
        return
    r = requests.get(cfg.DMS_URL.format(
        'GetVehiclesGroupByLocation', ''), auth=cfg.DMS_AUTH)
    if(r.status_code != 200):
        logger.error('Update "{}" caused error "{}" ({})'.format(
            bot, r.status_code, 'GetVehiclesGroupByLocation'))
        return False
    response = json.loads(r.text)
    for msg in response[:100]:
        update.message.reply_text(
            '{} = {}'.format(msg['Location'], msg['Cnt']))


def vehicleKeyboard(vehicleRef, action):
    r = requests.get(cfg.ODATA_URL.format(
        'Catalog_PhysicalLocations'), auth=cfg.DMS_AUTH)
    if(r.status_code != 200):
        logger.error('Update "%s" caused error %s',
                     r.status_code, 'Catalog_PhysicalLocations')
        return False

    j = json.loads(r.text)
    locations = j['value']
    keyboardLine = []
    for l in locations:
        btn = InlineKeyboardButton(
            l['Description'], callback_data='{}/{}/{}/{}'.format(vehicleRef, action, l['Code'], l['Description'][:10]))
        keyboardLine.append(btn)
    return keyboardLine
