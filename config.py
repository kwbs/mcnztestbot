import os
from requests.auth import HTTPBasicAuth

class Config(object):
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'KBKJHGFBGFDY$%#U$)#(UJOI!&(*@U(*'

class DMSConfig(Config):
    DMS_URL = 'http://1s.irktrans.com:8083/DMS_NZ/hs/DMSURL/{}?param={}'
    ODATA_URL = 'http://1s.irktrans.com:8083/DMS_NZ/odata/standard.odata/{}?$format=json'
    DMS_AUTH = HTTPBasicAuth('IBelov', '1722199')
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
    }