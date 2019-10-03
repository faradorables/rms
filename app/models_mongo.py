from datetime import datetime
import hashlib
import bleach
# from .models import Ion_User, Ion_Obu_List, Ion_Obu_Detail, Rdb_Client
from flask import current_app, request, url_for, Flask
from app.exceptions import ValidationError
from . import db, login_manager
from .utils import hmac_sha256
from . import mongo
import pymongo, requests
from bson import ObjectId
import os,time
from os.path import join, dirname, realpath

class TransLog:
    user_id = None
    wallet_id = None
    type_id = None
    type_name = None
    uid = None
    name = None
    accno = None
    accname = None
    billperiode = None
    nominal = None
    refca = None
    refsb = None
    serialno = None
    product_category_id = None
    product_category_name = None
    product_type_id = None
    product_type_name = None
    product_detail_name = None
    ref_id = None
    role_id = None
    provider = None
    image_name = None
    description = None
    amount = None
    _status = None
    time_add = None
    time_update = None
    time_end = None

    def _insert(self):
        response = {}
        timestamp = str(datetime.now())
        times = timestamp.split(" ")
        times = times[0].replace("-","")
        times = times.replace(".","")
        _data = {}
        if self.user_id != None:
            _data['user_id'] = self.user_id
            _data['wallet_id'] = self.wallet_id
            _data['type_id'] = self.type_id
            _data['type_name'] = self.type_name
            _data['uid'] = self.uid
            _data['name'] =	self.name
            _data['accno'] = self.accno
            _data['accname'] = self.accname
            _data['billperiode'] = self.billperiode
            _data['nominal'] = self.nominal
            _data['refca'] = self.refca
            _data['refsb'] = self.refsb
            _data['serialno'] =	self.serialno
            _data['product_category_id'] = self.product_category_id
            _data['product_category_name'] = self.product_category_name
            _data['product_type_id'] = self.product_type_id
            _data['product_type_name'] = self.product_type_name
            _data['product_detail_name'] = self.product_detail_name
            _data['ref_id'] = self.ref_id
            _data['role_id'] = self.role_id
            _data['provider'] =	self.provider
            _data['image_name'] = self.image_name
            _data['description'] = self.description
            _data['amount'] = self.amount
            _data['time_add'] = datetime.now()
            _data['time_update'] = datetime.now()
            _data['ref_id'] = str(self.type_id)+'.'+str(self.product_category_id)+'.'+str(self.user_id)+'.'+times
            if self.product_category_id == 1: #ION KONDISI INI NANTINYA UNTUK KEBUTUHAN PENGECEKAN TRANSAKSI PENDING SETIAP WAKTU TERTENTU SAMPAI TERUPDATE DENGAN SEMPURNA
                _data['time_end'] = datetime.now()
                if self._status == '00':
                    _data['_status'] = self._status
                elif self._status == '60':
                    _data['_status'] = self._status
                elif self._status == '70':
                    _data['_status'] = self._status
                elif self._status == '50':
                    _data['_status'] = self._status
            else:
                _data['time_end'] = datetime.now()
                if self._status == '00':
                    _data['_status'] = self._status
                elif self._status == '60':
                    _data['_status'] = self._status
                elif self._status == '70':
                    _data['_status'] = self._status
                elif self._status == '50':
                    _data['_status'] = self._status
            mongo.db.trx_log.insert(_data)
        else:
            response['_status'] = '50'
            response['messages'] = 'User Id tidak ada'

    def _list(self, user_id, _skip):
        response = {}
        response['data'] = []
        limit = 5
        if int(_skip) == 0:
            for i in mongo.db.trx_log.find({'user_id': int(user_id),'_status':'60'}).sort('time_update',pymongo.DESCENDING):
                print(i)
                time = i['time_update'].strftime("%H")+":"+i['time_update'].strftime("%M")
                response['data'].append({
                    'id': str(i['_id']),
                    '_status': i['_status'],
                    'amount': i['amount'],
                    'image_name': i['image_name'],
                    'product_category_name': i['product_category_name'],
                    'product_type_name': i['product_type_name'],
                    'date': i['time_update'].strftime("%a")+" "+i['time_update'].strftime("%d")+" "+i['time_update'].strftime("%b")+" "+i['time_update'].strftime("%Y")+", "+time
                })
        for i in mongo.db.trx_log.find({"$or": [{"$and" : [{'_status':'70'},{'user_id':int(user_id)}]},{"$and" : [{'_status':'50'},{'user_id':int(user_id)}]},{"$and" : [{'_status':'00'},{'user_id':int(user_id)}]}]}).sort('time_update',pymongo.DESCENDING).skip(int(_skip*limit)).limit(0):
            time = i['time_update'].strftime("%H")+":"+i['time_update'].strftime("%M")
            response['data'].append({
                'id': str(i['_id']),
                '_status': i['_status'],
                'amount': i['amount'],
                'image_name': i['image_name'],
                'product_category_name': i['product_category_name'],
                'product_type_name': i['product_type_name'],
                'date': i['time_update'].strftime("%a")+" "+i['time_update'].strftime("%d")+" "+i['time_update'].strftime("%b")+" "+i['time_update'].strftime("%Y")+", "+time
            })

        return response

    def _list_all(self, _skip):
        response = {}
        response['data'] = []
        limit = 5
        if int(_skip) == 0:
            for i in mongo.db.trx_log.find().sort('time_update',pymongo.DESCENDING):
                time = i['time_update'].strftime("%H")+":"+i['time_update'].strftime("%M")
                users = Ion_User.query.filter_by(id=i['user_id']).first()
                response['data'].append({
                    'user_id': i['user_id'],
                    'user_name': users.name,
                    'user_phone': users.phone_number,
                    'id': str(i['_id']),
                    '_status': i['_status'],
                    'amount': i['amount'],
                    'uid': i['uid'],
                    'image_name': i['image_name'],
                    'ref_id': i['ref_id'],
                    'name': i['name'],
                    'product_category_name': i['product_category_name'],
                    'product_type_name': i['product_type_name'],
                    'date': i['time_update'].strftime("%a")+" "+i['time_update'].strftime("%d")+" "+i['time_update'].strftime("%b")+" "+i['time_update'].strftime("%Y")+", "+time
                })

        return response

    def _list_highest(self, _skip):
        response = []
        limit = 5
        if int(_skip) == 0:
            for i in mongo.db.trx_log.find({'_status':'60'}).sort('amount',pymongo.DESCENDING):
                time = i['time_update'].strftime("%H")+":"+i['time_update'].strftime("%M")
                response.append({
                    'user_id': i['user_id'],
                    'id': str(i['_id']),
                    '_status': i['_status'],
                    'amount': i['amount'],
                    'image_name': i['image_name'],
                    'name': i['name'],
                    'product_category_name': i['product_category_name'],
                    'product_type_name': i['product_type_name'],
                    'date': i['time_update'].strftime("%a")+" "+i['time_update'].strftime("%d")+" "+i['time_update'].strftime("%b")+" "+i['time_update'].strftime("%Y")+", "+time
                })
        for i in mongo.db.trx_log.find({"$or": [{"$and" : [{'_status':'70'}]},{"$and" : [{'_status':'50'}]},{"$and" : [{'_status':'00'}]}]}).sort('amount',pymongo.DESCENDING).skip(int(_skip*limit)).limit(0):
            time = i['time_update'].strftime("%H")+":"+i['time_update'].strftime("%M")
            response.append({
                'user_id': i['user_id'],
                'id': str(i['_id']),
                '_status': i['_status'],
                'amount': i['amount'],
                'image_name': i['image_name'],
                'name': i['name'],
                'product_category_name': i['product_category_name'],
                'product_type_name': i['product_type_name'],
                'date': i['time_update'].strftime("%a")+" "+i['time_update'].strftime("%d")+" "+i['time_update'].strftime("%b")+" "+i['time_update'].strftime("%Y")+", "+time
            })

        return response

    def _update(self):
        response = {}
        timestamp = str(datetime.now())
        times = timestamp.split(" ")
        times = times[0].replace("-","")
        times = times.replace(".","")
        _byrefca = { "refca": self.refca }
        _update_status = { "$set": { "_status": self._status } }
        mongo.db.trx_log.update_one(_byrefca, _update_status)
        response['status'] = '00'
        response['messages'] = 'Sukses'
        return response

    def _data(self, user_id, _id):
        response = {}
        data = mongo.db.trx_log.find_one({
            '_id': ObjectId(_id)
        })
        if data is not None:
            time = data['time_update'].strftime("%H")+":"+data['time_update'].strftime("%M")
            if data['accno'] is not None:
                response['accno'] = data['accno']
            if data['accname'] is not None:
                response['accname'] = data['accname']
            if data['billperiode'] is not None:
                response['billperiode'] = data['billperiode']
            if data['nominal'] is not None:
                response['nominal'] = data['nominal']
            if data['serialno'] is not None:
                response['serialno'] = data['serialno']
            if data['refca'] is not None:
                response['refca'] = data['refca']
            if data['refsb'] is not None:
                response['refsb'] = data['refsb']
            if data['description'] is None:
                response['description'] = data['description']
            response['user_id'] = data['user_id']
            response['wallet_id'] = data['wallet_id']
            response['type_id'] = data['type_id']
            response['type_name'] = data['type_name']
            response['uid'] =data ['uid']
            response['name'] = data['name'].title()
            response['product_category_id'] = data['product_category_id']
            response['product_category_name'] = data['product_category_name']
            response['product_type_id'] = data['product_type_id']
            response['product_type_name'] = data['product_type_name']
            response['product_detail_name'] = data['product_detail_name']
            response['role_id'] = data['role_id']
            response['provider'] = data['provider']
            response['image_name'] = data['image_name']
            response['amount'] = data['amount']
            response['ref_id'] = data['ref_id']
            response['_status'] = data['_status']
            response['date'] = data['time_update'].strftime("%a")+" "+data['time_update'].strftime("%d")+" "+data['time_update'].strftime("%b")+" "+data['time_update'].strftime("%Y")+", "+time
        return response

    def _data_all(self, _id):
        response = {}
        data = mongo.db.trx_log.find_one({
            '_id': ObjectId(_id)
        })
        users = Ion_User.query.filter_by(id=data['user_id']).first()
        if data is not None:
            time = data['time_update'].strftime("%H")+":"+data['time_update'].strftime("%M")
            if data['accno'] is not None:
                response['accno'] = data['accno']
            if data['accname'] is not None:
                response['accname'] = data['accname']
            if data['billperiode'] is not None:
                response['billperiode'] = data['billperiode']
            if data['nominal'] is not None:
                response['nominal'] = data['nominal']
            if data['serialno'] is not None:
                response['serialno'] = data['serialno']
            if data['refca'] is not None:
                response['refca'] = data['refca']
            if data['refsb'] is not None:
                response['refsb'] = data['refsb']
            if data['description'] is None:
                response['description'] = data['description']
            response['user_id'] = data['user_id']
            response['wallet_id'] = data['wallet_id']
            response['type_id'] = data['type_id']
            response['type_name'] = data['type_name']
            response['uid'] = users.phone_number
            response['name'] = users.name
            response['product_category_id'] = data['product_category_id']
            response['product_category_name'] = data['product_category_name']
            response['product_type_id'] = data['product_type_id']
            response['product_type_name'] = data['product_type_name']
            response['product_detail_name'] = data['product_detail_name']
            response['role_id'] = data['role_id']
            response['provider'] = data['provider']
            response['image_name'] = data['image_name']
            response['amount'] = data['amount']
            response['ref_id'] = data['ref_id']
            response['_status'] = data['_status']
            response['date'] = data['time_update'].strftime("%a")+" "+data['time_update'].strftime("%d")+" "+data['time_update'].strftime("%b")+" "+data['time_update'].strftime("%Y")+", "+time
        return response

class Rapilog:
    obu_uid = None
    client_id = None
    client_name = None
    plaza_in_id = None
    plaza_in_name = None
    plaza_out_id = None
    plaza_out_name = None
    lane_id = None
    lane_name = None
    latitude_in = None
    longitude_in = None
    latitude_out = None
    longitude_out = None
    vehicle_class_id = None
    vehicle_class_name = None
    price = None
    time_in = datetime.now()
    time_out = datetime.now()
    refca_in = None
    refca_out = None
    status = None

    def _insert(self):
        response = {}
        _data = {}
        _data['obu_uid'] = self.obu_uid
        _data['client_id'] = self.client_id
        _data['client_name'] = self.client_name
        _data['plaza_in_id'] = self.plaza_in_id
        _data['plaza_in_name'] = self.plaza_in_name
        _data['plaza_out_id'] = self.plaza_out_id
        _data['plaza_out_name'] = self.plaza_out_name
        _data['lane_id'] = self.lane_id
        _data['lane_name'] = self.lane_name
        _data['latitude_in'] = self.latitude_in
        _data['longitude_in'] = self.longitude_in
        _data['latitude_out'] = self.latitude_out
        _data['longitude_out'] = self.longitude_out
        _data['vehicle_class_id'] = self.vehicle_class_id
        _data['vehicle_class_name'] = self.vehicle_class_name
        _data['price'] = self.price
        _data['time_in'] = self.time_in
        _data['time_out'] = self.time_in
        _data['refca_in'] = self.refca_in
        _data['refca_out'] = self.refca_out
        _data['status'] = self.status
        mongo.db.rapi_log.insert(_data)
        return response

    def _update(self):
        response = {}
        mongo.db.rapi_log.update({
            "obu_uid" : self.obu_uid, #multiple field
            "plaza_in_id" : self.plaza_in_id,
            "status" : "60"
        },
        { #field yang butuh untuk di update
            "$set" : { "plaza_out_id": self.plaza_out_id, "plaza_out_name": self.plaza_out_name, "price": self.price, "status" : self.status, "latitude_out" : self.latitude_out, "longitude_out" : self.longitude_out, "refca_out" : self.refca_out, "time_out": datetime.now()}
        })
        response['status'] = '00'
        response['messages'] = 'updated success'
        return response

    def _data(self, _obu_uid, _id):
        response = {}
        data = mongo.db.rapi_log.find_one({
            '_id': ObjectId(_id)
        })
        obulist = Ion_Obu_List.query.filter_by(obu_uid= _obu_uid, status=True).first()
        obudetail = Ion_Obu_Detail.query.filter_by(obu_id=obulist.id).first()
        user = Ion_User.query.filter_by(id=obudetail.user_id).first()
        if data is not None:
            response['obu_uid'] = data['obu_uid']
            response['user_name'] = user.name
            response['user_id'] = obudetail.user_id
            response['plate_id'] = obudetail.plate_id
            response['plaza_in_name'] = data['plaza_in_name']
            response['plaza_out_name'] = data['plaza_out_name']
            if data['plaza_out_name'] is None:
                response['plaza_out_name'] = '-'
            response['lane_in_name'] = data['lane_in_name']
            response['lane_out_name'] = data['lane_out_name']
            if data['lane_out_name'] is None:
                response['lane_out_name'] = '-'
            response['time_in'] = data['time_in']
            response['time_out'] = data['time_out']
            if data['time_out'] is None:
                response['time_out'] = '-'
            response['refca_in'] = data['refca_in']
            response['refca_out'] = data['refca_out']
            if data['refca_out'] is None:
                response['refca_out'] = '-'
            response['price'] = data['price']
            response['vehicle_class_name'] = data['vehicle_class_name']
            response['status'] = '00'
            response['messages'] = 'Data ditemukan'
        else:
            response['status'] = '50'
            response['messages'] = 'Data Tidak ada'
        return response

    def _list(self, client_id, _skip):
        response = {}
        response['client'] = []
        limit = 5
        if int(_skip) == 0:
            for i in mongo.db.rapi_log.find({'client_id': int(client_id)}):
                if i['plaza_out_id'] is not None:
                    response['client'].append({
                        'id': str(i['_id']),
                        'obu_uid': i['obu_uid'],
                        'plaza_in_name': i['plaza_in_name'],
                        'plaza_out_name': i['plaza_out_name'],
                        'price': i['price'],
                        'time_in': i['time_in']
                    })
                else:
                    response['client'].append({
                        'id': str(i['_id']),
                        'obu_uid': i['obu_uid'],
                        'plaza_in_name': i['plaza_in_name'],
                        'plaza_out_name': i['plaza_in_name'],
                        'price': i['price'],
                        'time_in': i['time_in']
                    })

        return response

    def _count(self, client_id):
        response = {}
        client = Rdb_Client.query.filter_by(ion_id=client_id).first()
        response ['total_trx'] = mongo.db.rapi_log.count()
        response ['client_trx'] = mongo.db.rapi_log.find({'client_id': int(client.id)}).count()
        return response
