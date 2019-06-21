from telegram import (ReplyKeyboardMarkup, ReplyKeyboardRemove)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters, RegexHandler,
                          ConversationHandler)

from telegram import ParseMode

import json
import logging
from config import DMSConfig as cfg
import requests
from dmsapi import checkLogin, findVehicle
import dmsapi
import statuses

logger = logging.getLogger(__name__)

COMPLIANCE_DEREG, COMPLIANCE_SEND, COMPLIANCE_RECEIVED, COMPLIANCE_ACTION, COMPLIANCE_SUPPLIER, COMPLIANCE_CAR, COMPLIANCE_STATUS = range(
    7)


def handler():
    compliance_handler = ConversationHandler(
        entry_points=[CommandHandler('compliance', compliance)],
        states={
            COMPLIANCE_CAR: [MessageHandler(Filters.text, compliance_car, pass_user_data=True)],
            COMPLIANCE_ACTION: [CommandHandler('send', compliance_send, pass_user_data=True), CommandHandler('receive', compliance_receive, pass_user_data=True)],
            COMPLIANCE_DEREG: [CommandHandler('dereg', compliance_dereg, pass_user_data=True), CommandHandler('skip', compliance_skip_dereg, pass_user_data=True)],
            COMPLIANCE_SUPPLIER: [MessageHandler(
                Filters.text, compliance_supplier, pass_user_data=True), CommandHandler('skip', compliance_skip_supplier, pass_user_data=True)],
            COMPLIANCE_STATUS: [CommandHandler('status', compliance_status, pass_user_data=True), CommandHandler(
                'skip', compliance_skip_status, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
        conversation_timeout=180,

    )
    return compliance_handler


def compliance(bot, update):
    if(not checkLogin(update.message.from_user, update)):
        return

    update.message.reply_text('Input a chasiss')

    return COMPLIANCE_CAR


def compliance_car(bot, update, user_data):

    vehicle = findVehicle(update.message.text)

    if(len(vehicle) == 0):
        update.message.reply_text(
            'No matches. Try other chassis number or /cancel workflow')
        return COMPLIANCE_CAR
    elif (len(vehicle) > 1):
        update.message.reply_text(
            'Found {} cars. Need to clarify chassis number. You can /cancel workflow'.format(len(vehicle)))
        for v in vehicle[:5]:
            update.message.reply_text('{} {} [{}]'.format(
                v['Make'], v['Model'], v['ChassisNo']))
        return COMPLIANCE_CAR

    v = vehicle[0]
    user_data.update(v)

    v_text = '{} {} [{}]'.format(v['Make'], v['Model'], v['ChassisNo'])
    try:
        url_template = 'https://s3-ap-southeast-2.amazonaws.com/pm-img/stock/{}-1.jpg'
        bot.send_photo(update.message.chat.id, photo=url_template.format(
            v['Pamir_uid']), caption=v_text)
    except:
        update.message.reply_text(v_text)

    compliance_doc = dmsapi.compliance_document(v['Ref'])

    if(compliance_doc.error):
        update.message.reply_text(compliance_doc.error_description)
        return ConversationHandler.END

    compliance_doc_count = len(compliance_doc.data)

    if(compliance_doc_count > 1):
        current_doc = compliance_doc.data[0]
        msg = 'Founded {} compliance documents, using the first: #{} dated {}'
        update.message.reply_text(msg.format(
            compliance_doc_count, current_doc['Number'], current_doc['Date']))

    elif(compliance_doc_count == 0):
        msg = 'No compliance task found. Creating a new task.'
        update.message.reply_text(msg)
        new_doc = dmsapi.compliance_document_new(v['Ref'])
        if(new_doc.error):
            update.message.reply_text(compliance_doc.error_description)
            return ConversationHandler.END
        current_doc = new_doc.data[0]

    elif(compliance_doc_count == 1):
        current_doc = compliance_doc.data[0]
        msg = 'Founded compliance task #{} dated {}'
        update.message.reply_text(msg.format(
            current_doc['Number'], current_doc['Date']))

    ud = user_data
    ud['compliance_doc'] = current_doc
    user_data.update(ud)

    reply_keyboard = [
        ['/send', '/receive'],
    ]
    update.message.reply_text('What we will doing?', reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True))

    return COMPLIANCE_ACTION


def compliance_send(bot, update, user_data):

    if(user_data['compliance_doc']['VehicleSent']):
        update.message.reply_text(
            'The vehicle already marked as "sent". Nothing to update.')

    else:
        res = dmsapi.compliance_set_send(
            user_data['compliance_doc']['Ref_Key'])
        if(res.error):
            update.message.reply_text(res.error_description)
            return ConversationHandler.END
        update.message.reply_text(
            'The vehicle marked as "sent" at current date.')

    reply_keyboard = [['/dereg', '/skip']]
    update.message.reply_text('Did you pass Dereg cert?', reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True))

    return COMPLIANCE_DEREG


def compliance_receive(bot, update, user_data):
    print('compliance_receive')
    print(user_data)
    update.message.reply_text('Action is under construction. Coming soon...')
    return ConversationHandler.END


def compliance_skip_send(bot, update, user_data):
    update.message.reply_text('The vehicle DID NOT mark as "sent".')

    reply_keyboard = [['/dereg', '/skip']]
    update.message.reply_text('Did you pass Dereg cert?', reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True))

    print('compliance_skip_send')    
    return COMPLIANCE_DEREG


def compliance_dereg(bot, update, user_data):
    res = dmsapi.compliance_set_dereg(user_data['compliance_doc']['Ref_Key'])
    if(res.error):
        update.message.reply_text(res.error_description)
        return ConversationHandler.END

    update.message.reply_text(
        'Tick "Dereg passed" updated. Please, type a supplier or /skip')
    return COMPLIANCE_SUPPLIER


def compliance_skip_dereg(bot, update, user_data):
    print('compliance_skip_dereg')    
    update.message.reply_text(
        'Dereg step skipped. Please, type a supplier or /skip')
    return COMPLIANCE_SUPPLIER


def compliance_supplier(bot, update, user_data):
    supplier = dmsapi.find_supplier(update.message.text)

    if(supplier.error):
        update.message.reply_text(supplier.error_description)
        return ConversationHandler.END

    if(len(supplier.data) == 0):
        update.message.reply_text(
            'No supplier found. Try again or /skip this step')
        return COMPLIANCE_SUPPLIER
    else:
        dmsapi.compliance_set_supplier(
            user_data['compliance_doc']['Ref_Key'], supplier.data[0]['Ref_Key'])

    update.message.reply_text('Supplier updated')
    reply_keyboard = [['/status', '/skip']]
    update.message.reply_text('Do you want update statuses and location (OUT / Pamir: At Compliance / DMS: At Compliance)?', reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True))

    return COMPLIANCE_STATUS


def compliance_skip_supplier(bot, update, user_data):
    print('compliance_skip_supplier ')    
    update.message.reply_text('Supplier NOT updated.')

    reply_keyboard = [['/status', '/skip']]
    update.message.reply_text('Do you want update statuses and location (OUT / Pamir: At Compliance / DMS: At Compliance)?', reply_markup=ReplyKeyboardMarkup(
        reply_keyboard, one_time_keyboard=True))

    return COMPLIANCE_STATUS


def compliance_status(bot, update, user_data):

    OUT_OF = '000000003'
    statuses.set_location(user_data['DMSID'], OUT_OF, update.message.chat.id)
    update.message.reply_text('Location set to "OUT"')

    AT_COMPLIANCE_DMS = '7ffe053c-890a-11e9-90f1-00155d580419'
    user_ref = None
    dms_status_result = statuses.set_dms_status(user_data['Ref'], AT_COMPLIANCE_DMS, user_ref)
    if(dms_status_result.error):
        update.message.reply_text(dms_status_result.error_description)
        return ConversationHandler.END

    update.message.reply_text('DMS status set to "At compliance"')

    AT_COMPLIANCE_PAMIR = '263'
    pamir_result = statuses.set_pamir_status(user_data['VehiclePricingId'], AT_COMPLIANCE_PAMIR)
    if(pamir_result.error):
        update.message.reply_text(pamir_result.error_description)
        return ConversationHandler.END        
    # TODO Set pamir status in 1C-DMS
    update.message.reply_text('Pamir status set to "At compliance"')

    update.message.reply_text('Done')
    
    return ConversationHandler.END


def compliance_skip_status(bot, update, user_data):
    update.message.reply_text('Statuses did not updated')
    update.message.reply_text('Done')
    return ConversationHandler.END


def cancel(bot, update):
    user = update.message.from_user
    logger.info("User %s canceled the conversation." % user.first_name)
    update.message.reply_text('Bye! I hope we can talk again some day.',
                              reply_markup=ReplyKeyboardRemove())

    return ConversationHandler.END
