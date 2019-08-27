from app import mongo
from random import randint
from flask import Flask, flash, jsonify
import re, pdb, string, random, os, requests, base64, datetime, hmac, hashlib, time, imaplib, email
from . import mongo
from datetime import datetime, date
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
from PIL import Image
import requests, json
apps = Flask(__name__)

def resize_files(_user_id, _image):
    response = {}
    PATH_FOLDER = join(dirname(realpath(__file__)), '../inbox/')
    apps.config['PATH_FOLDER'] = PATH_FOLDER
    filename, filename_ext = os.path.splitext(_image.filename)
    allowed_img = set(['png', 'jpg', 'jpeg'])
    if filename_ext.rsplit('.', 1)[1].lower() in allowed_img:
        _filename = str(_user_id)+'-'+str(time.time()).replace('.', '')+filename_ext
        getImage = Image.open(_image)
        # image_size = getImage.size
        # width = int(image_size[0])
        # height = int(image_size[1])
        # while(width>1000 or height>1000):
        #     width = int(width/2)
        #     height = int(height/2)
        # imgresize = getImage.resize((width, height), Image.ANTIALIAS)
        getImage.save(os.path.join(apps.config['PATH_FOLDER'], _filename))
        response['allowed'] = 'Sukses'
        response['status'] = '00'
        # response['name'] = _filename
        # response['image_id'] = _typeimage
    else :
        response['allowed'] = 'file tidak diizinkan'
        response['status'] = '60'
    return response


def hmac_sha256(key, msg):
    hash_obj = hmac.new(key=key, msg=msg, digestmod=hashlib.sha256)
    return hash_obj.hexdigest()

def generateRefca(user_id):
    return str(int(time.time())) + '#' + str(user_id)

class trxLog:
    user_id = None
    refca = None
    refsb = None
    status = None
    timestamp = datetime.utcnow()
    _accno = None
    _accname = None
    _phone_number = None
    _uid = None
    _name = None
    _description = None
    _type = None
    _billperiode = None
    _provider = None
    _cost = None
    _price = None
    _total_trx = None
    _detail = None

    def _insert(self):
        response = {}
        _data = {}
        _trx_log = mongo.db.trx_log
        if self.user_id != None:
            _data['user_id'] = self.user_id
            if self.refca == None:
                _data['refca'] = generateRefca(self.user_id)
            else:
                _data['refca'] = self.refca
            _data['refsb'] = self.refsb
            _data['status'] = self.status
            _data['timestamp'] = self.timestamp
            _data['_accno'] = self._accno
            _data['_accname'] = self._accname
            _data['_phone_number'] = self._phone_number
            _data['_uid'] = self._uid
            _data['_name'] = self._name
            _data['_description'] = self._description
            _data['_type'] = self._type
            _data['_billperiode'] = self._billperiode
            _data['_provider'] = self._provider
            _data['_cost'] = self._cost
            _data['_price'] = self._price
            _data['_total_trx'] = self._total_trx
            _data['_detail'] = self._detail
            _trx_log.insert(_data)
            response['status'] = '50'
            response['id'] = _data['refca']
        else:
            response['status'] = '50'
            response['message'] = 'ID User tidak ditemukan!'
        return response

def ip(ip_list):
    if ip_list.count(', ') == 1:
        ip1, ip3 = ip_list.split(', ')
        ip2 = 'None'
    elif ip_list.count(',') == 1:
        ip1, ip3 = ip_list.split(',')
        ip2 = 'None'
    elif ip_list.count(',') > 1:
        ip1, ip2, ip3 = ip_list.split(',')
    elif ip_list.count(', ') > 1:
        ip1, ip2, ip3 = ip_list.split(', ')
    else:
        raise ValueError(ip_list)
    return [ip1, ip2, ip3]

def user_log(url, ip_list):
    iplist = ip(ip_list)
    index_log = mongo.db.index_log
    index_log.insert({
        'user_id': current_user.id,
        'url': url,
        'ip_client': iplist[0],
        'ip_proxy': iplist[1],
        'ip_cloudflare': iplist[2],
        'timestamp': datetime.utcnow()
    })

def send_notif(firebase_id, title, body,status_upgrade, count, notif):
    headers = {
        'authorization' : 'key=AIzaSyAK1XTWAwyq-NGt38KHh9XdDPBTOeXImZo',
        'Content-Type' : 'application/json'
    }
    values = {
        "to" : firebase_id,
        "collapse_key" : "type_a",
        "notification" : {
            "title": title,
            "body" : body,
            "icon" : "notification_icon"
        },
        "data" : {
            "body" : "Body of Your Notification in Data",
            "title": "Title of Your Notification in Title",
            "status_upgrade": status_upgrade,
            "count": count,
            "notification": notif
        }
    }
    _request = requests.post('https://fcm.googleapis.com/fcm/send', data=json.dumps(values), headers=headers)
    _data = _request.json()
    print(_data)

class apiBCA:
    ApiKey = '34bec438-9911-494c-9e29-d0041f941eec'
    ApiSecret = 'f6068d37-0fd8-456a-bced-61ac35af53da'
    ClientId = 'b66925de-d8ec-476e-a170-6cf06c863b78'
    ClientSecret = 'efc71ced-b0e7-4b47-8270-3c24829764aa'
    DataAuth = str.encode(ClientId + ':' + ClientSecret)
    Auth = base64.b64encode(DataAuth)
    Authorization = 'Basic ' + Auth.decode()
    isoTimestamp = datetime.now().isoformat(timespec='milliseconds')
    timestamp = isoTimestamp + '+07:00'
    today_date = date.today().isoformat()

    def __init__(self,
                 CorporateID = 'h2hauto009' ,accNumber = '0613006572', url='https://devapi.klikbca.com:443',
                 startdate=today_date, enddate=today_date):
        self.CorporateID = CorporateID
        self.accNumber = accNumber
        self.url = url
        self.headers = {}
        self.data = []
        self.AccessToken = None
        self.startdate = startdate
        self.enddate = enddate

    def oAuth(self):
        self.headers = {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': self.Authorization,
        }
        self.data = [
            ('grant_type', 'client_credentials'),
        ]
        response = requests.post(self.url + '/api/oauth/token', headers=self.headers, data=self.data)
        return response.json()

    def generatesignature(self, accessToken, type='bi'):
        RelativeUrl = '/banking/v3/corporates/' + self.CorporateID + '/accounts/' + self.accNumber
        if type == 'as':
            RelativeUrl = '/banking/v3/corporates/' + self.CorporateID + '/accounts/' + self.accNumber + \
                          '/statements?EndDate=' + self.enddate + '&StartDate=' + self.startdate
        print(RelativeUrl)
        HTTPMethod = 'GET'
        RequestBody = hashlib.sha256(b"").hexdigest()
        StringToSign = str.encode(HTTPMethod + ":" + RelativeUrl + ":" + accessToken + ":" + RequestBody + ":" + self.timestamp)
        key = str.encode(self.ApiSecret)
        self.hmac_sha256(key, StringToSign)
        response = {
            'hcam': self.hmac_sha256(key, StringToSign),
            'timestamp': self.timestamp
        }
        print(StringToSign)
        return response

    def balanceInformation(self, accessToken, timestamp, signature):
        self.headers = {
            'Authorization': 'Bearer ' + accessToken,
            'Content-Type': 'application/json',
            'Origin': 'vinaya.tech',
            'X-BCA-Key': self.ApiKey,
            'X-BCA-Timestamp': timestamp,
            'X-BCA-Signature': signature,
        }

        response = requests.get(self.url + '/banking/v3/corporates/' + self.CorporateID + '/accounts/' + self.accNumber,
                                headers=self.headers)
        return response.json()

    def acountStatement(self, accessToken, timestamp, signature):
        self.headers = {
            'Authorization': 'Bearer ' + accessToken,
            'Content-Type': 'application/json',
            'Origin': 'vinaya.tech',
            'X-BCA-Key': self.ApiKey,
            'X-BCA-Timestamp': timestamp,
            'X-BCA-Signature': signature,
        }
        print(self.headers)
        response = requests.get(self.url + '/banking/v3/corporates/' + self.CorporateID + '/accounts/'
                                + self.accNumber + '/statements?EndDate=' + self.enddate + '&StartDate=' + self.startdate,
                                headers=self.headers)
        return response.json()


    def hmac_sha256(self, key, msg):
        hash_obj = hmac.new(key=key, msg=msg, digestmod=hashlib.sha256)
        return hash_obj.hexdigest()

    def uniqueNumber(self, array, saldo='50000'):
        rand = randint(0, 999)
        data = {}
        data['rc'] = 0
        if int(saldo) >= 50000:
            status = True
            unique_status = False
            while status:
                uc = int(saldo[-3:]) + rand
                total = int(saldo) + int(uc)
                uqc = str(total)[-3:]
                if len(array) > 0:
                    for i in array:
                        if i['uniquecode'] == uqc:
                            break
                        else:
                            unique_status = True
                            break
                    if unique_status == True:
                        data['rc'] = 1
                        data['saldo'] = total
                        data['uniquecode'] = str(total)[-3:]
                else:
                    data['rc'] = 1
                    data['saldo'] = total
                    data['uniquecode'] = str(total)[-3:]
                    unique_status = True
                if unique_status == True:
                    status = False
        return data



class _email:
    ORG_EMAIL = "@ion-network.id"
    _USER  = None
    _PWD = None
    _SERVER = "mx-s3.vivawebhost.com"

    def _auth(self):
        con = None
        if self._USER != None:
            con = imaplib.IMAP4_SSL(self._SERVER)
            _email = self._USER + self.ORG_EMAIL
            con.login(_email, self._PWD)
        return con
