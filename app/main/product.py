from flask import request, jsonify, redirect, url_for, app
from flask_login import login_required, current_user
from ..models import db, User
from datetime import datetime
from .. import mongo, csrf
from . import main
import xmlrpc.client, requests, time, json, xmltodict
from xmlrpc.server import SimpleXMLRPCServer
import copy


live_pass = "70675333"
devmode_pass = "12233344"
live_url = "https://api.siapbayar.com/v1/json"
devmode_url = "https://dev.siapbayar.com/api/v1/json"

@main.route('/request/saldo-payment', methods=['GET', 'POST'])
@login_required
def req_saldo_payment():
    if request.method == 'POST':
        data = User.query.filter_by(username=request.form['username']).first()
        if data == None:
            response = 'no_data.'
        elif data.username == current_user.username:
            response = 'no_data'
        else:
            if int(current_user.wallet) < int(request.form['trx_saldo']):
                response = 'no_saldo'
            else:
                current_user.wallet = str(int(current_user.wallet)-int(request.form['trx_saldo']))
                data.wallet = str(int(data.wallet) + int(request.form['trx_saldo']))
                history_log = mongo.db.history_log
                history_log.insert({
                    'user_id': current_user.id,
                    'productcode': 'trx_saldo',
                    'product_description': 'Transfer saldo kepada ' + str(data.name).capitalize(),
                    'refca': str(int(time.time())) + 'O' + str(current_user.id),
                    'accno': str(data.username),
                    'kubos_price': request.form['trx_saldo'],
                    'user_price': request.form['trx_saldo'],
                    'rc': '00',
                    'payment_type': 'Transfer Saldo',
                    'product_type': 'transfer_saldo',
                    # 'ip_client': iplist[0],
                    # 'ip_proxy': iplist[1],
                    # 'ip_cloudflare': iplist[2],
                    'timestamp': datetime.utcnow()
                })
                history_log.insert({
                    'user_id': data.id,
                    'productcode': 'trx_saldo',
                    'product_description': 'Transfer saldo dari ' + str(current_user.name).capitalize(),
                    'refca': str(int(time.time())) + 'O' + str(data.id),
                    'nohp': str(current_user.username),
                    'kubos_price': request.form['trx_saldo'],
                    'user_price': request.form['trx_saldo'],
                    'rc': '00',
                    'payment_type': 'Transfer Saldo',
                    'product_type': 'transfer_saldo',
                    # 'ip_client': iplist[0],
                    # 'ip_proxy': iplist[1],
                    # 'ip_cloudflare': iplist[2],
                    'timestamp': datetime.utcnow()
                })
                response = 'success'
                db.session.commit()
        return response
    else:
        return redirect(url_for('.index'))

@main.route('/request/payment/<section>', methods=['GET', 'POST'])
@login_required
def req_payment_prabayar(section):
    if request.method == 'POST':
        refca = str(int(time.time())) + 'O' + str(current_user.id)
        product_data = product_detail.query.filter_by(product_id=request.form['product_id']).first()
        user_price = mongo.db.user_price_list.find_one({
            'user_id': current_user.id
        })
        price = product_data.init_price
        if user_price != None:
            if request.form['product_id'] in user_price['product']:
                price = user_price['product'][request.form['product_id']]
        if section in ['pulsa_prabayar', 'data_prabayar', 'e_wallet', 'pln_prabayar']:
            if int(current_user.wallet) >= int(product_data.init_price):
                pay = prabayar_topup(refca, request.form['token_number'], request.form['product_id'])
                history = {}
                history['rc'] = pay['RESPONSECODE']
                history['user_id'] = current_user.id
                history['productcode'] = request.form['product_id']
                history['product_description'] = section.replace('_', ' ').capitalize() + ' (' + product_data.name + ')'
                history['product_type'] = section
                history['kubos_price'] = product_data.init_price
                history['user_price'] = price
                history['refca'] = refca
                history['accno'] = request.form['token_number']
                history['payment_type'] = section.replace('_', ' ').capitalize()
                # history['ip_client'] = iplist[0]
                # history['ip_proxy'] = iplist[1]
                # history['ip_cloudflare'] = iplist[2]
                history['timestamp'] = datetime.utcnow()
                if pay['RESPONSECODE'] == '00':
                    current_user.wallet = str(int(current_user.wallet) - int(product_data.init_price))
                    history['detail'] = {
                        'MSISDN': pay['MSISDN'],
                        'MESSAGE': pay['MESSAGE']
                    }
                    share_payment(current_user.id, section, request.form['product_id'], refca)
                elif pay['RESPONSECODE'] == '68':
                    current_user.wallet = str(int(current_user.wallet) - int(product_data.init_price))
                db.session.commit()
                history_log = mongo.db.history_log
                history_log.insert(history)
                response = {'rc': pay['RESPONSECODE']}
            else:
                response = {'rc': 'no_saldo'}
        elif section == 'voucher':
            if int(current_user.wallet) >= int(product_data.init_price):
                pay = voucher_topup(1, refca, request.form['token_number'], request.form['product_id'])
                history = {}
                history['rc'] = pay['rc']
                history['user_id'] = current_user.id
                history['productcode'] = request.form['product_id']
                history['product_description'] = section.replace('_', ' ').capitalize() + ' (' + product_data.name + ')'
                history['product_type'] = section
                history['kubos_price'] = product_data.init_price
                history['user_price'] = price
                history['refca'] = refca
                history['accno'] = request.form['token_number']
                history['payment_type'] = section.replace('_', ' ').capitalize()
                # history['ip_client'] = iplist[0]
                # history['ip_proxy'] = iplist[1]
                # history['ip_cloudflare'] = iplist[2]
                history['timestamp'] = datetime.utcnow()
                if pay['rc'] == '00':
                    current_user.wallet = str(int(current_user.wallet) - int(product_data.init_price))
                    history['detail'] = {
                        'info': pay['info'],
                        'trxtime': pay['trxtime'],
                        'serialno': pay['serialno'],
                        'refsb': pay['refsb']
                    }
                    share_payment(current_user.id, section, request.form['product_id'], refca)
                elif pay['rc'] == '68':
                    current_user.wallet = str(int(current_user.wallet) - int(product_data.init_price))
                db.session.commit()
                history_log = mongo.db.history_log
                history_log.insert(history)
                response = {'rc': pay['rc']}
            else:
                response = {'rc': 'no_saldo'}
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@main.route('/request/inquiry', methods=['GET', 'POST'])
@login_required
def req_inquiry():
    if request.method == 'POST':
        refca = str(int(time.time())) + 'O' + str(current_user.id)
        x = request.form
        if x['productcode'] == 'ASBPJSKS':
            billperiode = x['billperiode']
        else:
            billperiode = None
        req_data = inquiry(1, current_user.id, request.form['productcode'], request.form['token_number'], refca,
                           billperiode=billperiode)
        return jsonify(req_data)
    else:
        return redirect(url_for('.index'))

@main.route('/request/status', methods=['GET', 'POST'])
@login_required
def req_status():
    if request.method == 'POST':
        req_data = inq_status(1, current_user.id, request.form['productcode'], request.form['refca'], position=None)
        print(req_data)
        if req_data['rc'] == '00':
            data = {
                "refca": req_data['refca'],
                "accname": req_data['accname'],
                "accno": req_data['accno'],
                "billperiode": req_data['billperiode'],
                "nominal": req_data['nominal'],
                "price": str(int(req_data['price'])),
                "refsb": req_data['refsb'],
                "productcode": req_data['productcode'],
                "trxtime": time.time(),
            }
        elif req_data['rc'] == '':
            data = {
                "refca": req_data['refca'],
                "status": req_data['status'],
                "rc": req_data['rc'],
                "info": req_data['info'],
                "productcode": req_data['productcode'],
            }
        else:
            data = {}
        return jsonify(data)
    else:
        return redirect(url_for('.index'))

@main.route('/request/payment', methods=['GET', 'POST'])
@login_required
def req_payment_pascabayar():
    if request.method == 'POST':
        x = request.form
        if x['productcode'] == 'ASBPJSKS':
            billperiode = x['billperiode']
            nohp = x['nohp']
        else:
            billperiode = None
            nohp = None
        product_data = product_detail.query.filter_by(product_id=request.form['productcode']).first()
        user_price = mongo.db.user_price_list.find_one({
            'user_id': current_user.id
        })
        total_user_cost = (int(request.form['nominal']) + int(product_data.cost_fee))
        fee = int(product_data.cost_fee)
        if user_price != None:
            if request.form['productcode'] in user_price['product']:
                fee = int(user_price['product'][request.form['productcode']])

        if int(current_user.wallet) >= total_user_cost:
            print(request.form['refsb'])
            result = payment(
                0, current_user.id, request.form['productcode'], request.form['accno'],
                request.form['refca'], request.form['refsb'], request.form['nominal'],
                billperiode=billperiode, nohp=nohp
            )
            print(result)
            history = {}
            history['rc'] = result['rc']
            history['refca'] = result['refca']
            history['refsb'] = result['refsb']
            history['user_id'] = current_user.id
            history['productcode'] = result['productcode']
            history['product_description'] = request.form['type'].replace('_', ' ').capitalize() + ' (' + product_data.name + ')'
            history['product_type'] = request.form['type']
            history['kubos_fee'] = product_data.cost_fee
            history['user_fee'] = fee
            history['user_price'] = str(fee + int(result['nominal']))
            history['user_price'] = int(result['nominal'])
            history['accno'] = result['accno']
            history['payment_type'] = request.form['type'].replace('_', ' ').capitalize()
            # history['ip_client'] = iplist[0]
            # history['ip_proxy'] = iplist[1]
            # history['ip_cloudflare'] = iplist[2]
            history['timestamp'] = datetime.utcnow()
            if result['rc'] == '00':
                current_user.wallet = str(int(current_user.wallet) - total_user_cost)
                history['detail'] = {
                    'info': result['info'],
                    'accname': result['accname'],
                    'billperiode': result['billperiode'],
                    'trxtime': result['trxtime']
                }
                share_payment(current_user.id, request.form['type'], result['productcode'], result['refca'])
                response = 1
                history_log = mongo.db.history_log
                history_log.insert(history)
            elif result['rc'] == '' or result['rc'] == '68':
                current_user.wallet = str(int(current_user.wallet) - total_user_cost)
                response = 1
                history_log = mongo.db.history_log
                history_log.insert(history)
            elif result['rc'] in ['10', '11', '12', '13', '20', '21', '30', '31', '33', '35', '35', '90', '50']:
                response = 0
            elif result['rc'] in ['32', '36']:
                response = 0
            db.session.commit()
        else:
            response = 2
        return str(response)
    else:
        return redirect(url_for('.index'))

def prabayar_topup(refca, accno, product_id):
    with xmlrpc.client.ServerProxy("http://43.252.10.66:6793") as proxy:
        a =proxy.topUpRequest({
            'MSISDN': '08155176008',
            'PIN': '1234',
            'REQUESTID': refca,
            'NOHP': accno,
            'NOM': product_id
        })
    return a

def voucher_topup(status, refca, accno, product_id):
    if status == 1:
        url_req = live_url
        password = live_pass
    else:
        url_req = devmode_url
        password = devmode_pass
    payload = {
        "opcode": "game",
        "uid": "R0775",
        "pin": password,
        "productcode": product_id,
        "nohp": accno,
        "refca": refca
    }
    r = requests.post(url_req, json=payload)
    a = r.json()
    return a

def inquiry(status, current_user_id, productcode, accno, refca, billperiode=None):
    if status == 1:
        url_req = live_url
        password = live_pass
    else:
        url_req = devmode_url
        password = devmode_pass
    product_data = product_detail.query.filter_by(product_id=productcode).first()
    payload = {
        "opcode": "inquiry",
        "uid": "R0775",
        "pin": password,
        "productcode": productcode,
        "accno": accno,
        "refca": refca
    }
    if billperiode != None:
        payload['billperiode'] = billperiode
    r = requests.post(url_req, json=payload)
    req_data = r.json()
    user_price = mongo.db.user_price_list
    up = user_price.find_one({
        'user_id': current_user_id
    })
    print(req_data)
    price = product_data.cost_fee
    if up != None:
        if productcode in up['product']:
            price = up['product'][productcode]
    if req_data['rc'] == '00':
        data = {
            "rc": req_data['rc'],
            "info": req_data['info'],
            "status": "success",
            "refca": req_data['refca'],
            "refsb": req_data['refsb'],
            "productcode": req_data['productcode'],
            "accname": req_data['accname'],
            "accno": req_data['accno'],
            "billperiode": req_data['billperiode'],
            "admin_fee": price,
            "nominal": req_data['nominal'],
            "trxtime": time.time(),
        }
    elif req_data['rc'] == '':
        data = {
            "rc": req_data['rc'],
            "info": req_data['info'],
            "status": "pending",
            "refca": req_data['refca'],
            "productcode": productcode
        }
    else:
        data = {
            "rc": req_data['rc'],
            "status": "failed",
            "info": req_data['info'],
            "detail": req_data['info'].replace('Gagal.', '').replace('(', '').replace(')', '').strip()
        }
    return data

def inq_status(status, current_user_id, productcode, refca, position=None):
    if status == 1:
        url_req = live_url
        password = live_pass
    else:
        url_req = devmode_url
        password = devmode_pass
    product_data = product_detail.query.filter_by(product_id=productcode).first()
    payload = {
        "opcode": "status",
        "uid": "R0775",
        "pin": password,
        "refca": refca
    }
    r = requests.post(url_req, json=payload)
    req_data = r.json()
    user_price = mongo.db.user_price_list
    up = user_price.find_one({
        'user_id': current_user_id
    })
    price = product_data.cost_fee
    if up != None:
        if productcode in up['product']:
            price = up['product'][productcode]

    if req_data['rc'] == '00':
        data = {
            "rc": req_data['rc'],
            "info": req_data['info'],
            "status": "success",
            "refca": req_data['refca'],
            "refsb": req_data['refsb'],
            "productcode": req_data['productcode'],
            "accname": req_data['accname'],
            "accno": req_data['accno'],
            "billperiode": req_data['billperiode'],
            "admin_fee": price,
            "tagihan": req_data['nominal'],
            "trxtime": time.time(),
        }
    elif req_data['rc'] == '':
        data = {
            "rc": req_data['rc'],
            "info": req_data['info'],
            "status": "pending",
            "refca": req_data['refca'],
            "productcode": productcode
        }
    else:
        data = {
            "rc": req_data['rc'],
            "status": "failed",
            "info": req_data['info'],
            "detail": req_data['info'].replace('Gagal.', '').replace('(', '').replace(')', '').strip()
        }
    return data

def payment(status, current_user_id, productcode, accno, refca, refsb, nominal, billperiode=None, nohp=None):
    if status == 1:
        url_req = live_url
        password = live_pass
    else:
        url_req = devmode_url
        password = devmode_pass
    product_data = product_detail.query.filter_by(product_id=productcode).first()
    payload = {
        "opcode": "payment",
        "uid": "R0775",
        "pin": password,
        "productcode": productcode,
        "accno": accno,
        "nominal": nominal,
        "refca": refca,
        "refsbinq": refsb
    }
    print(payload)
    print(refsb)
    if billperiode != None:
        payload['billperiode'] = billperiode
        payload['nohp'] = nohp
    r = requests.post(url_req, json=payload)
    req_data = r.json()
    user_price = mongo.db.user_price_list
    up = user_price.find_one({
        'user_id': current_user_id
    })
    price = product_data.cost_fee
    if up != None:
        if productcode in up['product']:
            price = up['product'][productcode]
    print(req_data)
    data = {}
    data["rc"] = req_data['rc']
    data["info"] = req_data['info']
    data["refca"] = refca
    data["refsb"] = refsb
    data["productcode"] = productcode
    data["accno"] = accno
    data["admin_fee"] = price
    data ["nominal"] = nominal
    data["trxtime"] = time.time()
    if req_data['rc'] == '00':
        data["accname"] = req_data['accname']
        data["billperiode"] = req_data['billperiode']
    return data

def share_payment(current_user_id, product_type, product_id, user_refca):
    product_data = product_detail.query.filter_by(product_id=product_id).first()
    user = User().query.filter_by(id=current_user_id).first()
    admin = User().query.filter_by(role_id=1).first()
    distibutor_id = user.distributor_id if user.distributor_id is not None else None
    distibutor = User().query.filter_by(id=distibutor_id).first()
    reseller_id = user.reseller_id if user.reseller_id is not None else None
    reseller = User().query.filter_by(id=reseller_id).first()
    history_log = mongo.db.history_log
    price = product_data.init_price
    if product_data.init_price == None:
        price = product_data.cost_fee
    print(price)
    up = mongo.db.user_price_list.find_one({
        'user_id': current_user_id
    })
    if up != None:
        if product_id in up['product']:
            price = up['product'][product_id]
    history = {}
    history['rc'] = '00'
    history['user_refca'] = user_refca
    history['user_id'] = admin.id
    history['productcode'] = product_type
    history['product_description'] = product_type.replace('_', ' ').capitalize() + ' (' + product_data.name + ')'
    history['kubos_price'] = product_data.init_price
    history['downline_price'] = price
    history['product_type'] = 'pembagian_keuntungan'
    history['payment_type'] = 'Pembagian Keuntungan'
    history['timestamp'] = datetime.utcnow()
    if user.role_id == 1:
        user.wallet = str(int(user.wallet) + 750)
    elif user.role_id == 2:
        admin.wallet = str(int(admin.wallet) + 750)
        history['refca'] = str(int(time.time())) + 'O' + str(admin.id)
        history['user_price'] = 750
        history['accno'] = 'Distrobutor (' + user.username + ')'
        history_log.insert(history)
    elif user.role_id == 3:
        history_1 = copy.deepcopy(history)
        admin.wallet = str(int(admin.wallet) + 550)
        history['refca'] = str(int(time.time())) + 'O' + str(admin.id)
        history['user_price'] = 550
        history['accno'] = 'Reseller (' + user.username + ') - Distrobutor (' + distibutor.username + ')'
        history_log.insert(history)
        distibutor.wallet = str(int(distibutor.wallet) + 200)
        history_1['refca'] = str(int(time.time())) + 'O' + str(distibutor.id)
        history_1['user_price'] = 200
        history_1['accno'] = 'Reseller (' + user.username + ')'
        history_log.insert(history_1)
    elif user.role_id == 4:
        history_1 = copy.deepcopy(history)
        history_2 = copy.deepcopy(history)
        admin.wallet = str(int(admin.wallet) + 350)
        history['refca'] = str(int(time.time())) + 'O' + str(admin.id)
        history['user_price'] = 350
        history['accno'] = 'Downline (' + user.username + ') - Reseller (' + reseller.username + ') - Distrobutor (' + distibutor.username + ')'
        print(history)
        history_log.insert(history)
        distibutor.wallet = str(int(distibutor.wallet) + 200)
        history_1['refca'] = str(int(time.time())) + 'O' + str(distibutor.id)
        history_1['user_price'] = 200
        history_1['accno'] = 'Downline ('+user.username+') - Reseller (' + reseller.username + ')'
        print(history_1)
        history_log.insert(history_1)
        reseller.wallet = str(int(reseller.wallet) + 200)
        history_2['refca'] = str(int(time.time())) + 'O' + str(reseller.id)
        history_2['user_price'] = 200
        history_2['accno'] = 'Downline ('+user.username+')'
        print(history_2)
        history_log.insert(history_2)
    db.session.commit()

@main.route('/request/report/fastcom', methods=['GET', 'POST'])
@csrf.exempt
def req_report_fastcom():
    if request.method == 'POST':
        x = request.data
        jsonString = json.loads(json.dumps(xmltodict.parse(x), indent=4))
        datas = jsonString['methodCall']['params']['param']['value']['struct']['member']
        print(datas)
        RESPONSECODE = ''
        for i in datas:
            if i['name'] == 'REQUESTID':
                REQUESTID = i['value']['string']
                print(REQUESTID)
            elif i['name'] == 'MSISDN':
                MSISDN = i['value']['string']
                print(MSISDN)
            elif i['name'] == 'RESPONSECODE':
                RESPONSECODE = i['value']['string']
                print(RESPONSECODE)
            elif i['name'] == 'MESSAGE':
                MESSAGE = i['value']['string']
                print(MESSAGE)
            if RESPONSECODE == '00':
                SN = ''
                if i['name'] == 'SN':
                    SN = i['value']['string']
                print(SN)
        history_log = mongo.db.history_log
        data = history_log.find_one({'refca': REQUESTID})
        print(data)
        user = User().query.filter_by(id=data['user_id']).first()
        print(user)
        # print(user.id)
        print(user.wallet)
        history_data = {
            'rc': RESPONSECODE,
            'detail': {
                'MSISDN': MSISDN,
                'MESSAGE': MESSAGE
            }
        }
        # print(history_data)
        if RESPONSECODE == '00':
            history_data['detail']['SN'] = SN
            user.wallet = str(int(user.wallet) - int(data['kubos_price']))
            share_payment(user.id, data['product_type'], data['productcode'], REQUESTID)
        if RESPONSECODE not in ['00', '68']:
            user.wallet = str(int(user.wallet) + int(data['kubos_price']))
        db.session.commit()
        # print(history_data)
        history_log.update({
            'refca': REQUESTID
        }, {
            '$set': history_data
        })
        return 'DONE'
    else:
        return redirect(url_for('.index'))
