import json
import logging
from dataclasses import dataclass, field
from datetime import datetime

import requests

from config import DMSConfig as cfg

logger = logging.getLogger(__name__)


@dataclass
class Response:
    error: bool = False
    error_description: str = ''
    data: list = field(default_factory=list)


def set_location(vehicle_code: str, location_code: str, telegram_user: str):
    result = Response()
    param = json.dumps({'locationCode': location_code,
                        'vehicleCode': vehicle_code,
                        'telegramUser': telegram_user})
    r = requests.get(cfg.DMS_URL.format(
        'SetVehicleLocation', param), auth=cfg.DMS_AUTH)

    if(r.text != 'OK'):
        result.error = True
        result.error_description = 'set_location() error'

    return result


def set_pamir_status(vehicle_pamir_stockid: str, status_code: str):
    result = Response()
    url = "https://api.pamir.co.nz/v1/private/stock/change-status"

    headers = {'Authorization': 'Bearer 56b701de166646ecaca092ea72749cc1',
               'Content-Type': 'application/json'
               }

    data = {'stock_id': vehicle_pamir_stockid,
            'status': status_code,
            'comments': 'via Telegram'
            }

    r = requests.post(url, data=json.dumps(data), headers=headers)    
    if(r.status_code!=200):
        result.error = True
        result.error_description = 'Error {}\nPlease send a screenshot to @Belov_Ilia'.format(r.text)
    return result


def set_dms_status(vehicle_ref: str, status_ref: str, user_ref: str):
    result = Response()
    rec = {
        'Period': datetime.now().isoformat(),
        'Vehicle_Key': vehicle_ref,
        'Status_Key': status_ref,
        'User_Key': user_ref,
    }
    
    url = cfg.ODATA_URL.format('InformationRegister_StatusDMS')
    
    r = requests.post(url, auth=cfg.DMS_AUTH,
                      headers=cfg.headers, data=json.dumps(rec))
    print(url)
    print(json.dumps(rec))
    if(r.status_code != 200):
        result.error = True
        result.error_description = '1C-DMS error set_dms_status(). Try /compliance later. {} [{}]\nPlease report to @Belov_Ilia'.format(
            r.status_code, url)
        logger.error(result.error_description)

    return result
