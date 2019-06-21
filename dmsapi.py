from config import DMSConfig as cfg
import requests
import logging
import json
from telegram import ParseMode
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class Response:
    error: bool = False
    error_description: str = ''
    data: list = field(default_factory=list)


def checkLogin(user, update):
    user_id = update.message.from_user.id
    ODATA_URL_filter = cfg.ODATA_URL + '&$filter=TelegramID eq {}'
    r = requests.get(ODATA_URL_filter.format(
        'Catalog_TelegramUsers', user_id), auth=cfg.DMS_AUTH)
    if(r.status_code != 200):
        logger.error('Update caused error "{}" ({})'.format(
            r.status_code, 'Catalog_TelegramUsers'))
        return False
    response = json.loads(r.text)

    approved = False
    for u in response['value']:
        if ((not u['DeletionMark']) and (u['Approved'])):
            approved = True

    # TODO return AUTH object for certain user for 1C-DMS login
    if(approved):
        return True
    else:
        update.message.reply_text('You have <b>no permissions</b>.'
                                  'Use /login command and wait for approval.'
                                  'If any question contact @Belov_Ilia or belov.penrose@gmail.com', parse_mode=ParseMode.HTML)
        return False


def findVehicle(chassis):
    r = requests.get(cfg.DMS_URL.format(
        'GetVehicles', chassis), auth=cfg.DMS_AUTH)

    if(r.status_code != 200):
        logger.error('Update caused error "{}" ({})'.format(
            r.status_code, 'GetVehicles at findVehicle()'))
        return []

    return json.loads(r.text)


def compliance_document_new(VehicleRef):
    ''' Create new compliance task'''
    result = Response()

    doc = {
        'Date': datetime.now().isoformat(),
        'Vehicle_Key': VehicleRef,
        'Posted': True,
        'Comments': 'Via @PamirNZBot'
    }

    url = cfg.ODATA_URL.format('Document_Compliance')

    r = requests.post(url, auth=cfg.DMS_AUTH,
                      headers=cfg.headers, data=json.dumps(doc))

    if(r.status_code != 201):
        result.error = True
        result.error_description = '1C-DMS error compliance_document_new(). Try /compliance later. {} [{}]'.format(
            r.status_code, url)
        logger.error(result.error_description)

    result.data = [json.loads(r.text)]

    return result


def compliance_document(VehicleRef):
    ''' Find compliance document '''

    url_template = cfg.ODATA_URL + "&$filter=Posted eq true and Vehicle_Key eq guid'{}'"
    url = url_template.format('Document_Compliance', VehicleRef)
    r = requests.get(url, auth=cfg.DMS_AUTH)

    result = Response()

    if(r.status_code != 200):
        result.error = True
        result.error_description = '1C-DMS error compliance_document() {} [{}]. Try /compliance again.'.format(
            r.status_code, url)
        logger.error(result.error_description)

    result.data = json.loads(r.text)['value']
    return result


def compliance_set_send(ComplianceDocRef):
    ''' set tick "car sent" '''
    result = Response()
    doc_ref = "Document_Compliance(guid'{}')".format(ComplianceDocRef)
    url = cfg.ODATA_URL.format(doc_ref)

    doc = {
        'VehicleSent': True,
        'VehicleSentDate': datetime.now().isoformat()
    }

    r = requests.patch(url, auth=cfg.DMS_AUTH,
                       headers=cfg.headers, data=json.dumps(doc))

    if(r.status_code != 200):
        result.error = True
        result.error_description = '1C-DMS error compliance_set_send() {} [{}]. Try /compliance again.'.format(
            r.status_code, url)
        logger.error(result.error_description)

    return result


def compliance_set_dereg(ComplianceDocRef):
    ''' Set tick "dereg passed" '''
    result = Response()
    doc_ref = "Document_Compliance(guid'{}')".format(ComplianceDocRef)
    url = cfg.ODATA_URL.format(doc_ref)

    doc = {
        'DeregPassed': True,
        'DeregPassedDate': datetime.now().isoformat()
    }

    r = requests.patch(url, auth=cfg.DMS_AUTH,
                       headers=cfg.headers, data=json.dumps(doc))

    if(r.status_code != 200):
        result.error = True
        result.error_description = '1C-DMS error compliance_set_dereg() {} [{}]. Try /compliance again.'.format(
            r.status_code, url)
        logger.error(result.error_description)

    return result


def compliance_set_supplier(ComplianceDocRef, SupplierRef):
    ''' Set supplier to compliance task '''
    result = Response()
    doc_ref = "Document_Compliance(guid'{}')".format(ComplianceDocRef)
    url = cfg.ODATA_URL.format(doc_ref)
    doc = {'Supplier_Key': SupplierRef}
    r = requests.patch(url, auth=cfg.DMS_AUTH,
                       headers=cfg.headers, data=json.dumps(doc))
    if(r.status_code != 200):
        result.error = True
        result.error_description = '1C-DMS error compliance_set_dereg() {} [{}]. Try /compliance again.'.format(
            r.status_code, url)
        logger.error(result.error_description)

    return result


def find_supplier(search_string):
    ''' Find supplier '''
    result = Response()
    filter = "&$filter=DeletionMark eq false and TelegramName eq '{}'".format(
        search_string)
    url = cfg.ODATA_URL.format('Catalog_Contacts') + filter
    r = requests.get(url, auth=cfg.DMS_AUTH)
    if(r.status_code != 200):
        result.error = True
        result.error_description = '1C-DMS error compliance_set_dereg() {} [{}]. Try /compliance again.'.format(
            r.status_code, url)
        logger.error(result.error_description)

    result.data = json.loads(r.text)['value']

    return result
