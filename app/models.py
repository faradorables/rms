from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
import bleach
from flask import current_app, request, url_for, Flask
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
from .utils import hmac_sha256
from . import mongo
import pymongo, requests
from bson import ObjectId
import os,time
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename
from sqlalchemy import func, desc, asc, extract
import flask_excel as excel

# engine = create_engine('mysql://root@localhost:3306/ams')
apps = Flask(__name__)
excel.init_excel(apps)

@login_manager.user_loader
def load_user(user_id):
    return Ion_User.query.get(int(user_id))

class Role(db.Model):
    __tablename__ = 'ams_roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def _insert_data():
        roles = {
            'Super Admin',
            'Authenticator',
        }
        for r in roles:
            role = Role()
            role.name = r
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

    def _list(self):
        response = []
        role = Role.query.filter_by(status=True).all()
        for u in role:
            response.append({
                'id': u.id,
                'name': u.name,
            })
        return response

class User(UserMixin, db.Model):
    __tablename__ = 'ams_users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(64))
    password_hash = db.Column(db.String(128))
    pin_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('ams_roles.id'), default=2)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _name, _phone, _email, _password, _pin, _role_id):
        _user = User()
        _user.name=_name
        _user.phone_number=_phone
        _user.email=_email
        _user.password=_password
        _user.pin=_pin
        _user.role_id= _role_id
        db.session.add(_user)
        db.session.commit()
        token = _user.generate_token()
        response = User()._data(_user.id)
        return response

    def _insert_new_user(self, _name, _phone):
        _user = User()
        _user.name = _name
        _user.phone_number = _phone
        db.session.add(_user)
        db.session.commit()

    def _setPin(self, _id, _pin):
        _user = User.query.filter_by(id=_id, status=True).first()
        _user.pin = _pin
        db.session.add(_user)
        db.session.commit()
        token = _user.generate_token()
        response = User()._data(_user.id, token)
        return response

    def _data(self, _id): #untuk membaca data user kebutuhan transaksi
        response = {}
        user = User.query.filter_by(id=_id, status=True).first()
        role = Role.query.filter_by(id=user.role_id).first()
        response['id'] = _id
        response['phone'] = user.phone_number
        response['name'] = user.name
        response['email'] = user.email
        response['role_id'] = user.role_id
        response['role_name'] = role.name
        # response['referral'] = user.referral
        return response

    def _update(self, _id, _user_id, _name, _phone, _email,  _new_id,  _role_id=1): #untuk membaca data kebutuhan read data untuk di update nantinya
        _user = User.query.filter_by(id=_id, status=True).first()
        _user.id=_user_id
        _user.name=_name
        _user.phone_number=_phone
        _user.email=_email
        _user.id=_new_id
        _user.role_id= _role_id
        db.session.add(_user)
        db.session.commit()
        token = _user.generate_token()
        response = User()._data(_user.id)
        return response

    def _list(self, limit=25, page=0):
        response = []
        page = page * limit
        user = User.query.filter_by(status=True).offset(page).limit(limit).all()
        for u in user:
            # role_name = Role.query.filter_by(id=u.id).first()
            role = Role.query.filter_by(id=u.role_id).first()
            print(role)
            response.append({
                'id': u.id,
                'name': u.name,
                'phone': u.phone_number,
                'email': u.email if u.email != None else '-',
                'role_id': u.role_id,
                'role_name': role.name
            })
        return response

    def _count(self):
        response = {}
        response['total_admins'] = User.query.count()
        response['active_admins'] = User.query.filter_by(status=True).count()
        response['passive_admins'] = User.query.filter_by(status=False).count()
        return response

    def _delete(self, _id):
        _user = User.query.filter_by(id=_id).first()
        _user.status = False
        db.session.add(_user)
        db.session.commit()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def pin(self):
        raise AttributeError('pin is not a readable attribute')

    @password.setter
    def pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def verify_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)

    def generate_token(self):
        key = str.encode(self.phone_number)
        msg = str.encode(str(self.id) + ':' + str(self.role_id) + ':' + str(self.name) + ':' + str(self.phone_number) + ':' + str(self.email) + ':' + str(self.pin_hash))
        return hmac_sha256(key, msg)

    def verify_token(self, token):
        response = False
        key = str.encode(self.phone_number)
        msg = str.encode(str(self.id) + ':' + str(self.role_id) + ':' + str(self.name) + ':' + str(self.phone_number) + ':' + str(self.email) + ':' + str(self.pin_hash))
        if token == hmac_sha256(key, msg):
            response = True
        return response

    def ping(self):
        self.last_seen = datetime.now()
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def _insert_data():
        User()._insert('Yehuda Dani Utomo', '08155176008', 'yeye@ion-network.id', '!2345ion5432!', '123456',  _role_id=1 )
        User()._insert('Farah Shahnaz Imami', '08975181009', 'farah@ion-network.id', '!2345ion5432!', '123456',  _role_id=1)
        User()._insert('Tes', '1234', 'tes@ion-network.id', '!2345ion5432!', '123456',  _role_id=1)
        User()._insert('Admin 2', '081234567890', 'admin@ion-network.id', '!2345ion5432!', '123456', _role_id=2)
        print('Done!')

class Subject_Support(db.Model):
    __bind_key__= 'users'
    __tablename__ = 'ams_subject_support'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    supports =  db.relationship('Support', backref='subject_support', lazy='dynamic')

    @staticmethod
    def _insert_data():
        subjects = {
            'ION Cash',
            'OBU',
            'Payment',
            'Account',
        }
        for s in subjects:
            subject = Subject_Support()
            subject.name = s
            db.session.add(subject)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

    def _list(self):
        response = []
        subject = Subject_Support.query.filter_by(status=True).all()
        for s in subject:
            response.append({
                'id': s.id,
                'name': s.name,
            })
        return response

class Status_Support(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ams_status_support'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    supports =  db.relationship('Support', backref='status_support', lazy='dynamic')

    @staticmethod
    def _insert_data():
        status = {
            'Solved',
            'On Process',
            'Unsolved',
            'Cancelled',
        }
        for s in status:
            stat = Status_Support()
            stat.name = s
            db.session.add(stat)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

    def _list(self):
        response = []
        stat = Status_Support.query.filter_by(status=True).all()
        for s in stat:
            response.append({
                'id': s.id,
                'name': s.name,
            })
        return response

class Support(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ams_support'
    id = db.Column(db.Integer, primary_key=True)
    id_user = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    id_subject = db.Column(db.Integer, db.ForeignKey('ams_subject_support.id'))
    id_status = db.Column(db.Integer, db.ForeignKey('ams_status_support.id'), default=1)
    ticket_number = db.Column(db.String(64), unique=True)
    title = db.Column(db.String(64), unique=True)
    description = db.Column(db.String(512))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _count(self):
        response = {}
        response['total_support'] = Support.query.count()
        response['total_onprocess'] = Support.query.filter_by(id_status=4).count()
        response['total_unsolved'] = Support.query.filter_by(id_status=3).count()
        response['total_solved'] = Support.query.filter_by(id_status=2).count()
        response['total_cancelled'] = Support.query.filter_by(id_status=1).count()
        return response

    def _data(self, _id): #untuk membaca data supports
        response = {}
        support = Support.query.filter_by(id=_id, status=True).first()
        subject = Subject_Support.query.filter_by(id=support.id_subject).first()
        status = Status_Support.query.filter_by(id=support.id_status).first()
        user = Ion_User.query.filter_by(id=support.id_user).first()
        response['id'] = _id
        response['id_subject'] = support.id_subject
        response['id_status'] = support.id_status
        response['id_user'] = support.id_user
        response['ticket_number'] = support.ticket_number
        response['name_subject'] = subject.name
        response['name_status'] = status.name
        response['name_user'] = user.name
        response['title'] = support.title
        response['description'] = support.description
        return response

    def _list(self, limit=25, page=0):
        response = []
        page = page * limit
        support = Support.query.filter_by(status=True).offset(page).limit(limit).all()
        for s in support:
            subject = Subject_Support.query.filter_by(id=s.id_subject).first()
            status = Status_Support.query.filter_by(id=s.id_status).first()
            users = Ion_User.query.filter_by(id=s.id_user).first()
            print(subject)
            response.append({
                'id': s.id,
                'id_user': s.id_user,
                'id_subject': s.id_subject,
                'id_status': s.id_status,
                'ticket_number': s.ticket_number,
                'name_subject': subject.name,
                'name_status': status.name,
                'title': s.title,
                'description': s.description
            })
        return response

    def _insert(self, _id_subject, _id_status, _title, _description):
        _support = Support()
        _support.id_subject=_id_subject
        _support.id_status=_id_status
        _support.title=_title
        _support.description=_description
        db.session.add(_support)
        db.session.commit()
        response = Support()._data(_support.id)
        return response

    @staticmethod
    def _insert_data():
        Support()._insert('2', '2', 'Cant make a payment', 'user cannot make a payment')
        print('Done!')

class Rdb_Client(db.Model):
    __bind_key__ = 'toll'
    __tablename__ = 'clients'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    nickname = db.Column(db.String(64))
    address = db.Column(db.String(128))
    phone = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    trx_type_id = db.Column(db.Integer, db.ForeignKey('transaction_type.id'))
    # logo_id = db.Column(db.Integer, db.ForeignKey('gallery.id'))
    ion_id = db.Column(db.Integer)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    plaza = db.relationship('Rdb_Plaza', backref='role', lazy='dynamic')


    @staticmethod
    def _insert_data():
        values = [
            {"name" : "PT Citra Marga Nusaphala Persadar", "nickname": "CMNP", "address" : "Jalan. Kemayoran", "phone": "02178989222", "email" : "citra_marga@cmnp.com", "trx_type_id": 1, "logo_id" : 1, "ion_id": 1},
            {"name" : "PT Jasamarga", "nickname": "JM", "address" : "Jalan. jasamarga", "phone": "021700012247", "email" : "jasa_marga@jm.com", "trx_type_id": 2, "logo_id" : 2, "ion_id": 2}
        ]
        for v in values:
            _client = Rdb_Client()
            _client.name = v['name']
            _client.nickname = v['nickname']
            _client.address = v['address']
            _client.phone = v['phone']
            _client.email = v['email']
            _client.trx_type_id = v['trx_type_id']
            _client.logo_id = v['logo_id']
            _client.ion_id = v['ion_id']
            db.session.add(_client)
            db.session.commit()

    def _insert(self, _name, _phone, _email, _ion_id, _trx_type):
        _client = Rdb_Client()
        _client.name= _name
        _client.phone_number= _phone
        _client.email= _email
        _client.ion_id = _ion_id
        _client.trx_type_id = _trx_type
        # _client.logo_id = '1'
        db.session.add(_client)
        db.session.commit()
        # token = _client.generate_token()
        response = Rdb_Client()._data(_client.id)
        return response

    def _data(self, client_id): #untuk membaca data user kebutuhan transaksi
        response = {}
        client = Rdb_Client.query.filter_by(id=client_id, status=True).first()
        if client is not None:
            response['id'] = client_id
            response['phone'] = client.phone_number
            response['name'] = client.name
            response['email'] = client.email
        return response

class Rdb_Transaction_Type(db.Model):
    __bind_key__ = 'toll'
    __tablename__ = 'transaction_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = ['Open', 'CLose']
        for v in values:
            _type = Rdb_Transaction_Type()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

    def _list(self):
        response = []
        trxtype = Rdb_Transaction_Type.query.filter_by(status=True).all()
        for u in trxtype:
            response.append({
                'id': u.id,
                'name': u.name,
            })
        return response

class Rdb_Plaza(db.Model):
    __bind_key__ = 'toll'
    __tablename__ = 'plaza'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    address = db.Column(db.String(512))
    image = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "Tol A", "client_id": 1, "latitude" : 1.0821982829, "longitude": 2.1299029188, "address" : "Jalan. A", "image": "335112664651158001989.png"},
            {"name" : "Tol B", "client_id": 2, "latitude" : 2.3244443434, "longitude": 2.4240324024, "address" : "Jalan. B", "image": "324231114434324243243.png"},
            {"name" : "Tol C", "client_id": 2, "latitude" : 2.4288843242, "longitude": 2.4042426324, "address" : "Jalan. C", "image": "324231114434324243243.png"},
            {"name" : "Tol D", "client_id": 2, "latitude" : 1.0078843242, "longitude": 1.9900002224, "address" : "Jalan. C", "image": "324231114434324243243.png"}
        ]
        for v in values:
            _plaza = Plaza()
            _plaza.name = v['name']
            _plaza.client_id = v['client_id']
            _plaza.latitude = v['latitude']
            _plaza.longitude = v['longitude']
            _plaza.address = v['address']
            _plaza.image = v['image']
            db.session.add(_plaza)
            db.session.commit()

    def _list(self, _client_id, limit=25, page=0):
        response = []
        page = page * limit
        client = Rdb_Client.query.filter_by(ion_id=_client_id).first()
        _list = Rdb_Plaza.query.filter_by(client_id=client.id, status=True).all()
        for i in _list:
            response.append({
                'plaza_id': i.id,
                'name': i.name,
                'address': i.address,
                'latitude': i.latitude,
                'longitude': i.longitude,
                'image': i.image
            })
        return response

    def _list_append(self, _client_id):
        response = []
        client = Rdb_Client.query.filter_by(ion_id=_client_id).first()
        _list = Rdb_Plaza.query.filter_by(client_id=client.id, status=True).all()
        for i in _list:
            response.append({
                'plaza_id': i.id,
                'name': i.name
            })
        return response

    def _insert(self, _name, _client_id, _latitude, _longitude, _address, _image):
        _plaza = Rdb_Plaza()
        _plaza.name=_name
        _plaza.client_id=_client_id
        _plaza.latitude=_latitude
        _plaza.longitude=_longitude
        _plaza.address=_address
        _plaza.image=_image
        db.session.add(_plaza)
        db.session.commit()
        response = Rdb_Plaza()._data(_plaza.id)
        print(_plaza.id)
        return response

    def _data(self, plaza_id): #untuk membaca data user kebutuhan transaksi
        response = {}
        plaza = Rdb_Plaza.query.filter_by(id=plaza_id).first()
        client = Rdb_Client.query.filter_by(id=plaza.client_id).first()
        total_lane = Rdb_Lane.query.filter_by(plaza_id=plaza_id).count()
        if plaza is not None:
            response['id'] = plaza_id
            response['name'] = plaza.name
            response['address'] = plaza.address
            response['latitude'] = plaza.latitude
            response['longitude'] = plaza.longitude
            response['client'] = client.name
            response['total_lane'] = total_lane
        return response

    def _update(self, _id, _name, _client_id, _latitude, _longitude, _address, _image): #untuk membaca data kebutuhan read data untuk di update nantinya
        _plaza = Rdb_Plaza.query.filter_by(id=_id, status=True).first()
        _plaza.name=_name
        _plaza.client_id=_client_id
        _plaza.latitude=_latitude
        _plaza.longitude=_longitude
        _plaza.address=_address
        _plaza.image=_image
        db.session.add(_plaza)
        db.session.commit()
        response = Rdb_Plaza()._data(_plaza.id)
        print(_plaza.id)
        return response

class Rdb_Lane_Type(db.Model):
    __bind_key__ = 'toll'
    __tablename__ = 'lane_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    lane = db.relationship('Rdb_Lane', backref='role', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ['In', 'Out']
        for v in values:
            _type = Rdb_Lane_Type()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

    def _list(self):
        response = []
        type = Rdb_Lane_Type.query.filter_by(status=True).all()
        for u in type:
            response.append({
                'id': u.id,
                'name': u.name,
            })
        return response

class Rdb_Lane(db.Model):
    __bind_key__ = 'toll'
    __tablename__ = 'lane'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    lane_type_id = db.Column(db.Integer, db.ForeignKey('lane_type.id'))
    plaza_id = db.Column(db.Integer, db.ForeignKey('plaza.id'))
    added_time = db.Column(db.DateTime(), default=datetime.utcnow)
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "lane 1A", "lane_type_id": 1, "plaza_id": 1},
            {"name" : "lane 2A", "lane_type_id": 1, "plaza_id": 1},
            {"name" : "lane 1B", "lane_type_id": 1, "plaza_id": 2},
            {"name" : "lane 2B", "lane_type_id": 2, "plaza_id": 3},
            {"name" : "lane 1C", "lane_type_id": 1, "plaza_id": 3},
            {"name" : "lane 2C", "lane_type_id": 2, "plaza_id": 4}
        ]
        for v in values:
            _lane = Rdb_Lane()
            _lane.name = v['name']
            _lane.lane_type_id = v['lane_type_id']
            _lane.plaza_id = v['plaza_id']
            db.session.add(_lane)
            db.session.commit()

    def _list(self, plaza_id):
        response = []
        _list = Rdb_Lane.query.filter_by(plaza_id=plaza_id, status=True).all()
        for i in _list:
            lane_type = Rdb_Lane_Type.query.filter_by(id=i.lane_type_id).first()
            response.append({
                'id':i.id,
                'lane_name': i.name,
                'lane_type': lane_type.name
            })
        return response

    def _insert(self, _name, _lane_type_id, _plaza_id):
        _lane = Rdb_Lane()
        _lane.name=_name
        _lane.lane_type_id=_lane_type_id
        _lane.plaza_id=_plaza_id
        db.session.add(_lane)
        db.session.commit()
        response = Rdb_Lane()._data(_lane.id)
        print(_lane.id)
        return response

    def _data(self, _lane_id): #untuk membaca data user kebutuhan transaksi
        response = {}
        lane = Rdb_Lane.query.filter_by(id=_lane_id).first()
        type = Rdb_Lane_Type.query.filter_by(id=lane.lane_type_id).first()
        if lane is not None:
            response['id'] = _lane_id
            response['name'] = lane.name
            response['type'] = type.name
            response['type_id'] = type.id
        return response

    def _update(self, _id, _name, _lane_type_id, _plaza_id):
        _lane = Rdb_Lane.query.filter_by(id=_id, status=True).first()
        _lane.name=_name
        _lane.lane_type_id=_lane_type_id
        _lane.plaza_id=_plaza_id
        db.session.add(_lane)
        db.session.commit()
        response = Rdb_Lane()._data(_lane.id)
        print(_lane.id)
        return response

class Rdb_Price(db.Model):
    __bind_key__ = 'toll'
    __tablename__ = 'price'
    id = db.Column(db.Integer, primary_key=True)
    plaza_in_id = db.Column(db.Integer, db.ForeignKey('plaza.id'))
    plaza_out_id = db.Column(db.Integer, db.ForeignKey('plaza.id'))
    vehicle_class_id = db.Column(db.Integer, db.ForeignKey('vehicle_class.id'))
    price = db.Column(db.Integer)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"plaza_in_id" : 1, "plaza_out_id" : None, "vehicle_class_id" : 1, "price": 7500},
            {"plaza_in_id" : 1, "plaza_out_id" : None, "vehicle_class_id" : 2, "price": 9000},
            {"plaza_in_id" : 2, "plaza_out_id" : 2, "vehicle_class_id" : 1, "price": 10000},
            {"plaza_in_id" : 2, "plaza_out_id" : 2, "vehicle_class_id" : 2, "price": 12000},
            {"plaza_in_id" : 2, "plaza_out_id" : 3, "vehicle_class_id" : 1, "price": 8000},
            {"plaza_in_id" : 2, "plaza_out_id" : 3, "vehicle_class_id" : 2, "price": 10000},
            {"plaza_in_id" : 2, "plaza_out_id" : 4, "vehicle_class_id" : 1, "price": 13000},
            {"plaza_in_id" : 2, "plaza_out_id" : 4, "vehicle_class_id" : 2, "price": 18000},
            {"plaza_in_id" : 3, "plaza_out_id" : 4, "vehicle_class_id" : 1, "price": 13000},
            {"plaza_in_id" : 3, "plaza_out_id" : 4, "vehicle_class_id" : 2, "price": 18000}
        ]
        for v in values:
            _price = Rdb_Price()
            _price.plaza_in_id = v['plaza_in_id']
            _price.plaza_out_id = v['plaza_out_id']
            _price.vehicle_class_id = v['vehicle_class_id']
            _price.price = v['price']
            db.session.add(_price)
            db.session.commit()

    def _list(self, client_id, limit=25, page=0):
        response = []
        page = page * limit
        print(client_id)
        client = Rdb_Client.query.filter_by(id=client_id, status=True).first()
        trx_type = Rdb_Transaction_Type.query.filter_by(id=client.trx_type_id, status=True).first()
        print(trx_type)
        if trx_type.id == 1: #1 trx type = open
            _list = Rdb_Price.query.filter_by(status=True).all()
            print(_list)
            for i in _list:
                plaza_in = Rdb_Plaza.query.filter_by(id=i.plaza_in_id).first()
                if plaza_in.client_id == client_id:
                    response.append({
                        'id': i.id,
                        'plaza_in': plaza_in.name,
                        'price': i.price,
                        'vehicle_class': i.vehicle_class_id
                    })
        else:
            _list = Rdb_Price.query.filter_by(status=True).all()
            print(_list)
            for i in _list:
                plaza_in = Rdb_Plaza.query.filter_by(id=i.plaza_in_id).first()
                if plaza_in.client_id == client_id:
                    plaza_out = Rdb_Plaza.query.filter_by(id=i.plaza_out_id).first()
                    response.append({
                        'id': i.id,
                        'plaza_in': plaza_in.name,
                        'plaza_out': plaza_out.name,
                        'price': i.price,
                        'vehicle_class': i.vehicle_class_id
                    })
        return response

    def _insert(self, plaza_in_id, plaza_out_id, vehicle_class_id, price):
        _price = Rdb_Price()
        _price.plaza_in_id=plaza_in_id
        _price.plaza_out_id=plaza_out_id
        _price.vehicle_class_id=vehicle_class_id
        _price.price=price
        db.session.add(_price)
        db.session.commit()
        response = Rdb_Price()._data(_price.id)
        return response

    def _data(self, price_id): #untuk membaca data user kebutuhan transaksi
        response = {}
        price = Rdb_Price.query.filter_by(id=price_id).first()
        plaza_in = Rdb_Plaza.query.filter_by(id=price.plaza_in_id).first()
        plaza_out = Rdb_Plaza.query.filter_by(id=price.plaza_out_id).first()
        print(price)
        if price is not None:
            response['id'] = price_id
            response['plaza_in'] = plaza_in.name
            response['plaza_in_id'] = plaza_in.id
            response['plaza_out'] = plaza_out.name
            response['plaza_out_id'] = plaza_out.id
            response['vehicle_class'] = price.vehicle_class_id
            response['price'] = price.price
        return response

    def _update(self, _id, plaza_in, plaza_out, vehicle_class, price): #untuk membaca data kebutuhan read data untuk di update nantinya
        _price = Rdb_Price.query.filter_by(id=_id, status=True).first()
        _price.plaza_in_id=plaza_in
        _price.plaza_out_id=plaza_out
        _price.vehicle_class_id=vehicle_class
        _price.price=price
        db.session.add(_price)
        db.session.commit()
        response = Rdb_Price()._data(_price.id)
        return response

class Rdb_Vehicle_Class(db.Model):
    __bind_key__ = 'toll'
    __tablename__ = 'vehicle_class'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    price = db.relationship('Rdb_Price', backref='role', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ['Golongan 1', 'Golongan 2']
        for v in values:
            _class = Rdb_Vehicle_Class()
            _class.name = v
            db.session.add(_class)
            db.session.commit()

    def _list(self):
        response = []
        vehicle = Rdb_Vehicle_Class.query.all()
        for u in vehicle:
            response.append({
                'id': u.id,
                'name': u.name
            })
        return response

class Rdb_User(UserMixin, db.Model):
    __bind_key__='toll'
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    username = db.Column(db.String(64))
    password = db.Column(db.String(128))
    email = db.Column(db.String(64), unique=True, index=True)
    phone_number = db.Column(db.String(64), unique=True, index=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "CMNP", "username": "cmnp2019", "password" : "abcdefghij", "address" : "Jalan username", "email" : "citra_marga@cmnp.com", "phone_number": "02178989222", "client_id": 1, "role_id" : 1},
            {"name" : "JM", "username": "jasamarga2019", "password" : "jasamarga", "address" : "Jalan jasamarga", "email" : "jasa_marga@cmnp.com", "phone_number": "0213332092", "client_id": 2, "role_id" : 1}
        ]
        for v in values:
            _user = Rdb_User()
            _user.name = v['name']
            _user.username = v['username']
            _user.password = v['password']
            _user.email = v['email']
            _user.address = v['address']
            _user.phone_number = v['phone_number']
            _user.client_id = v['client_id']
            _user.role_id = v['role_id']
            db.session.add(_user)
            db.session.commit()

class Ion_Role(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    users = db.relationship('Ion_User', backref='role', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ['User', 'BUJT', 'Merchant']
        for v in values:
            role = Ion_Role()
            role.name = v
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class Ion_User(UserMixin, db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(64))
    pin_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('ion_roles.id'), default=1)
    firebase_id = db.Column(db.String(255))
    tos_agreement = db.Column(db.Boolean, default=False)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)
    confirmed = db.Column(db.Boolean, default=True)
    id_upgrade = db.Column(db.Integer, db.ForeignKey('ion_upgrade.id'))
    verified = db.Column(db.Boolean, default=False)

    bank_account = db.relationship('Ion_Bank_Account', backref='User', lazy='dynamic')
    identity = db.relationship('Ion_Identity', backref='User', lazy='dynamic')
    wallet = db.relationship('Ion_Wallet', backref='User', lazy='dynamic')
    correspondent_address = db.relationship('Ion_Correspondent_Address', backref='User', lazy='dynamic')
    obu_list = db.relationship('Ion_Obu_List', backref='User', lazy='dynamic')
    obu_detail = db.relationship('Ion_Obu_Detail', backref='User', lazy='dynamic')
    bank_account = db.relationship('Ion_Bank_Account', backref='User', lazy='dynamic')
    point = db.relationship('Ion_Point', backref='User', lazy='dynamic')
    image_service = db.relationship('Ion_Image_Service', backref='User', lazy='dynamic')
    log_activity = db.relationship('Ion_Log_Activity', backref='User', lazy='dynamic')
    supports =  db.relationship('Support', backref='User', lazy='dynamic')

    def _list(self, limit=25, page=0):
        response = []
        page = page * limit
        user = Ion_User.query.filter_by(role_id=1).offset(page).limit(limit).all()
        for u in user:
            response.append({
                'id': u.id,
                'name': u.name,
                'phone_number': u.phone_number,
                'email': u.email if u.email != None else '-',
                'wallet': Ion_Wallet()._check(u.id),
                'added_time': u.added_time.year,
                'id_upgrade': u.id_upgrade
            })
        return response

    def _list_upgraded(self, limit=25, page=0):
        response = []
        page = page * limit
        user = Ion_User.query.filter_by(role_id=1).filter(Ion_User.id_upgrade != None).filter(Ion_Upgrade.status==True).order_by(Ion_User.id.asc()).offset(page).limit(limit).all()
        for u in user:
            response.append({
                'id': u.id,
                'name': u.name,
                'phone_number': u.phone_number,
                'email': u.email if u.email != None else '-',
                'wallet': Ion_Wallet()._check(u.id),
                'added_time': u.added_time.year,
                'id_upgrade': u.id_upgrade
            })
        return response

    def _list_suspended(self, limit=25, page=0):
        response = []
        page = page * limit
        user = Ion_User.query.filter_by(status=False, role_id=1).order_by(Ion_User.id.asc()).offset(page).limit(limit).all()
        for u in user:
            response.append({
                'id': u.id,
                'name': u.name,
                'phone_number': u.phone_number,
                'email': u.email if u.email != None else '-',
                'wallet': Ion_Wallet()._check(u.id),
                'added_time': u.added_time.year,
                'id_upgrade': u.id_upgrade
            })
        return response

    def _list_bujt(self, limit=25, page=0):
        response = []
        page = page * limit
        user = Ion_User.query.filter_by(role_id=2).offset(page).limit(limit).all()
        for u in user:
            client = Rdb_Client.query.filter(Rdb_Client.ion_id == u.id).first()
            response.append({
                'id': u.id,
                'name': u.name,
                'phone_number': u.phone_number,
                'email': u.email if u.email != None else '-',
                'wallet': Ion_Wallet()._check(u.id),
                'added_time': u.added_time.year,
                'client_id': client.id,
            })
        return response

    def _count(self, _client_id):
        response = {}
        client = Rdb_Client.query.filter_by(ion_id=_client_id).first()
        response['total_plaza'] = Rdb_Plaza.query.filter_by(client_id = client.id).count()
        response['total_bujt'] = Ion_User.query.filter_by(role_id=2).count()
        response['active_user'] = Ion_User.query.join(Ion_Wallet, Ion_User.id == Ion_Wallet.user_id).group_by(Ion_User.id).filter(Ion_Wallet.type_id == 1).filter(Ion_Wallet.amount > 0).filter(Ion_User.role_id == 1).count()
        response['active_bujt'] = Ion_User.query.join(Ion_Wallet, Ion_User.id == Ion_Wallet.user_id).group_by(Ion_User.id).filter(Ion_Wallet.type_id == 1).filter(Ion_Wallet.amount > 0).filter(Ion_User.role_id == 2).count()
        response['users_request_upgrade'] = Ion_Upgrade.query.filter_by(status=True).filter(Ion_Upgrade.status_upgrade_id == 1).count()
        print(client.id)
        return response

    def _insert(self, _name, _phone):
        _user = Ion_User()
        _user.name=_name
        _user.phone_number=_phone
        _user.tos_agreement = True
        db.session.add(_user)
        db.session.commit()
        token = _user.generate_token()
        response = User()._data(_user.id, token)
        return response

    def _insert_client(self, _name, _phone, _email, _trx_type, _pin):
        _user = Ion_User()
        _client = Rdb_Client()
        _user.name= _name
        _user.phone_number= _phone
        _user.email= _email
        _client.trx_type_id= _trx_type
        _user.pin= _pin
        _user.role_id = 2
        _user.tos_agreement = True
        db.session.add(_user)
        db.session.commit()
        client = Rdb_Client()._insert(_user.name, _user.phone_number, _user.email, _user.id, _client.trx_type_id)
        token = _user.generate_token()
        response = Ion_User()._data(_user.id), client
        return response

    def _loginNotif(self, _id, _fbaseId):
        _user = Ion_User.query.filter_by(id=_id).first()
        _user.firebase_id = _fbaseId
        db.session.add(_user)
        db.session.commit()

    def _setPin(self, _id, _pin):
        _user = Ion_User.query.filter_by(id=_id, status=True).first()
        _user.pin = _pin
        db.session.add(_user)
        db.session.commit()
        token = _user.generate_token()
        response = Ion_User()._data(_user.id, token)
        return response

    def _data(self, user_id): #untuk membaca data user kebutuhan transaksi
        response = {}
        obu = Ion_Obu_List.query.filter_by(user_id=user_id, status=True).first()
        user = Ion_User.query.filter_by(id=user_id, status=True).first()
        total_obu = Ion_Obu_List.query.filter_by(user_id=user_id, status=True).count()
        total_trx = Ion_Wallet.query.filter_by(user_id=user_id, status=True).count()
        upgrade = Ion_Upgrade.query.filter_by(user_id=user_id).first()
        client = Rdb_Client.query.filter_by(ion_id=user_id).first()
        if user is not None:
            response['id'] = user_id
            response['phone'] = user.phone_number
            response['name'] = user.name
            response['email'] = user.email
            response['id_upgrade'] = user.id_upgrade
            response['wallet'] = Ion_Wallet()._check(user.id)
            response['user_trx'] = Ion_Wallet()._user_trx(user.id)
            response['client_trx'] = total_trx
            response['total_obu'] = total_obu
            if upgrade is not None:
                response['status_upgrade'] = upgrade.status_upgrade_id
            else:
                response['status_upgrade'] = 'Unknown'
            if client is not None:
                response['client_id'] = client.id
            else:
                response['client_id'] = 'Unknown'
        else:
            response['id'] = 'Unknown'
            response['phone'] = 'Unknown'
            response['name'] = 'Unknown'
            response['email'] = 'Unknown'
            response['id_upgrade'] = 'None'
            response['wallet'] = 'Unknown'
            response['total_obu'] = 'Unknown'
        return response

    def _update(self, _id, _name, _email): #untuk membaca data kebutuhan read data untuk di update nantinya
        _user = Ion_User.query.filter_by(id=_id, status=True).first()
        _user.name=_name
        _user.email=_email
        db.session.add(_user)
        db.session.commit()
        token = _user.generate_token()
        response = Ion_User()._data(_user.id, token)
        return response

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def pin(self):
        raise AttributeError('pin is not a readable attribute')

    @password.setter
    def pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def verify_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)

    def generate_token(self):
        key = str.encode(self.phone_number)
        msg = str.encode(str(self.id) + ':' + str(self.role_id) + ':' + str(self.name) + ':' + str(self.phone_number) + ':' + str(self.email) + ':' + str(self.pin_hash))
        return hmac_sha256(key, msg)

    def verify_token(self, token):
        response = False
        key = str.encode(self.phone_number)
        msg = str.encode(str(self.id) + ':' + str(self.role_id) + ':' + str(self.name) + ':' + str(self.phone_number) + ':' + str(self.email) + ':' + str(self.pin_hash))
        if token == hmac_sha256(key, msg):
            response = True
        return response

    def ping(self):
        self.last_seen = datetime.now()
        db.session.add(self)
        db.session.commit()

class Ion_Identity(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_identity'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    profile_photo = db.Column(db.String(128))
    nik = db.Column(db.String(128))
    province_id = db.Column(db.Integer, db.ForeignKey('ion_province.id'))
    city_id = db.Column(db.Integer, db.ForeignKey('ion_city.id'))
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('ion_kecamatan.id'))
    kelurahan_id = db.Column(db.Integer, db.ForeignKey('ion_kelurahan.id'))
    address = db.Column(db.String(128))
    postal_code_id = db.Column(db.Integer, db.ForeignKey('ion_postal_code.id'))
    photo_ktp = db.Column(db.String(128))
    selfie_idcard = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _user_id, _profil_photo, _nik, _province_id, _city_id, _kecamatan_id, _kelurahan_id, _address, _postal_code, _photo_ktp, _selfie_idcard):
        _identity = Ion_Identity()
        _identity.user_id = _user_id
        _identity.profile_photo = _profil_photo
        _identity.nik = _nik
        _identity.province_id = _province_id
        _identity.city_id = _city_id
        _identity.kecamatan_id = _kecamatan_id
        _identity.kelurahan_id = _kelurahan_id
        _identity.address = _address
        _identity.postal_code_id = _postal_code
        _identity.photo_ktp = _photo_ktp
        _identity.selfie_idcard = _selfie_idcard
        db.session.add(_identity)
        db.session.commit()

    def _data(self, _id):
        response = {}
        _ident = Ion_Identity.query.filter_by(user_id=_id, status=True).first()
        response['id'] = _ident.id
        response['user_id'] = _ident.user_id
        response['profile_photo'] = _ident.profile_photo
        response['nik'] = _ident.nik
        response['province_id'] = _ident.province_id
        response['city_id'] = _ident.city_id
        response['kecamatan_id'] = _ident.kecamatan_id
        response['kelurahan_id'] = _ident.kelurahan_id
        response['address'] = _ident.address
        response['postal_code_id'] = _ident.postal_code_id
        response['photo_ktp'] = _ident.photo_ktp
        response['selfie_idcard'] = _ident.selfie_idcard
        return response

    def _update(self, _id, _user_id, _profil_photo, _nik, _province_id, _city_id, _kecamatan_id, _kelurahan_id, _address, _postal_code, _photo_ktp, _selfie_idcard):
        _identity = Ion_Identity()
        _identity.user_id = _user_id
        _identity.profile_photo = _photo
        _identity.nik = _nik
        _identity.province_id = _province_id
        _identity.city_id = _city_id
        _identity.kecamatan_id = _kecamatan_id
        _identity.kelurahan_id = _kelurahan_id
        _identity.address = _address
        _identity.postal_code_id = _postal_code
        _identity.photo_ktp = _ktpname
        _identity.selfie_idcard = _selfieId
        db.session.add(_identity) #insert data baru dengan status true
        db.session.commit()
        response = Ion_Identity()._data(_identity.user_id)
        return response

    def _delete(self, _id):
        _identity = Ion_Identity.query.filter_by(id=_id, status=True).first()
        _identity.status = False #set status false
        db.session.add(_identity) #update status false untuk data sebelumnya
        db.session.commit()

class Ion_Correspondent_Address(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_correspondent_address'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    province_id = db.Column(db.Integer, db.ForeignKey('ion_province.id'))
    city_id = db.Column(db.Integer, db.ForeignKey('ion_city.id'))
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('ion_kecamatan.id'))
    kelurahan_id = db.Column(db.Integer, db.ForeignKey('ion_kelurahan.id'))
    postal_code_id = db.Column(db.Integer, db.ForeignKey('ion_postal_code.id'))
    address_detail = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _user_id, _province_id, _city_id, _kecamatan_id, _kelurahan_id, _postal_code_id, _address_detail):
        _corres_address = Ion_Correspondent_address()
        _corres_address.province_id = _province_id
        _corres_address.user_id = _user_id
        _corres_address.city_id = _city_id
        _corres_address.kecamatan_id = _kecamatan_id
        _corres_address.kelurahan_id = _kelurahan_id
        _corres_address.postal_code_id = _postal_code_id
        _corres_address.address_detail = _address_detail
        db.session.add(_corres_address)
        db.session.commit()

    def _data(self, _user_id):
        response = {}
        _read = Ion_Correspondent_address.query.filter_by(user_id=_user_id, status=True).first()
        response['id'] = _read.id
        response['user_id'] = _read.user_id
        response['province_id'] = _read.province_id
        response['city_id'] = _read.city_id
        response['kecamatan_id'] = _read.kecamatan_id
        response['kelurahan_id'] = _read.kelurahan_id
        response['postal_code_id'] = _read.postal_code_id
        response['address_detail'] = _read.address_detail
        return response

    def _update(self, _user_id, _province_id, _city_id, _kecamatan_id, _kelurahan_id, _postal_code_id, _address_detail):
        response = {}
        _corres_address = Ion_Correspondent_address.query.filter_by(user_id=_user_id).first()
        _corres_address.province_id = _province_id
        _corres_address.user_id = _user_id
        _corres_address.city_id = _city_id
        _corres_address.kecamatan_id = _kecamatan_id
        _corres_address.kelurahan_id = _kelurahan_id
        _corres_address.postal_code_id = _postal_code_id
        _corres_address.address_detail = _address_detail
        db.session.add(_corres_address)
        db.session.commit()
        return response

    def _delete(self, _id):
        _identity = Ion_Correspondent_address.query.filter_by(id=_id, status=True).first()
        _identity.status = False #set status false
        db.session.add(_identity) #update status false untuk data sebelumnya
        db.session.commit()

class Ion_Bank_List(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_bank_list'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    uid = db.Column(db.String(64), unique=True, index=True)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    bank_account = db.relationship('Ion_Bank_Account', backref='Bank_List', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ["BRI", "BCA", "BNI", "MANDIRI"]
        for v in values:
            _bank = Ion_Bank_List()
            _bank.name = v
            db.session.add(_bank)
            db.session.commit()

class Ion_Bank_Account(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_bank_account'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(124))
    account_number = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    bank_id = db.Column(db.Integer, db.ForeignKey('ion_bank_list.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Ion_Wallet(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_wallet'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('ion_activity_wallet.id'))
    amount = db.Column(db.Integer, default=0)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    #melakukan check saldo pada table wallet berdasarkan id
    def _check(self, _id):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        user = Ion_User.query.filter_by(id=_id).first()
        if user is not None:
            _wallet = Ion_Wallet.query.filter_by(user_id=user.id, status=True).all()
            for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
                if i.type_id == 1: #status 1 adalah debit
                    debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
                elif i.type_id == 2: #status 2 adalah credit
                    credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet(self):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_client(self):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        client = Ion_User.query.filter_by(role_id=2, status=True).all()
        for c in client:
            _wallet = Ion_Wallet.query.filter_by(user_id=c.id ,status=True).all()
            for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
                if i.type_id == 1: #status 1 adalah debit
                    debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
                elif i.type_id == 2: #status 2 adalah credit
                    credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
            response = debit - credit
        return response

    def _total_trx(self):
        response = {}
        trx = 0
        _wallet = Ion_Wallet.query.filter_by(status=True).all()
        _request = Ion_Request()._request_amount()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            trx += i.amount
        response = trx - _request
        return response

    def _user_trx(self, _id):
        response = {}
        trx = 0
        user = Ion_User.query.filter_by(id=_id).first()
        if user is not None:
            _wallet = Ion_Wallet.query.filter_by(user_id=user.id, status=True).all()
            for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
                trx += i.amount
        response = trx
        return response

    def _total_wallet_jan(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 1).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_feb(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 2).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_mar(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 3).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_apr(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 4).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_may(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 5).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_jun(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 6).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_jul(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 7).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_agt(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 8).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_sep(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 9).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_oct(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 10).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_nov(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 11).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _total_wallet_des(self, year):
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        _wallet = Ion_Wallet.query.filter(extract('month',Ion_Wallet.added_time) == 12).filter(extract('year',Ion_Wallet.added_time) == year).filter_by(status=True).all()
        for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            if i.type_id == 1: #status 1 adalah debit
                debit += i.amount #debit = debit(0) nilai awal yang telah di set + nominal yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
            elif i.type_id == 2: #status 2 adalah credit
                credit += i.amount #credit = credit(0) nilai awal yang telah di set + nominal yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _insert(self, _id, _type, _nominal):
        _wallet = Ion_Wallet()
        _wallet.user_id = _id
        _wallet.type_id = int(_type)
        _wallet.amount = _nominal
        _wallet.added_time =  datetime.now()
        db.session.add(_wallet)
        db.session.commit()
        response = Ion_Wallet()._data(_wallet.id, _id)
        return response

    def _data(self, user_id, _id):
        response = {}
        _wallet = Ion_Wallet.query.filter_by(id=_id, user_id=user_id, status=True).first()
        if _wallet is not None:
            response['id'] = _wallet.id
            response['user_id'] = _wallet.user_id
            response['nominal'] = _wallet.amount
            response['timestamp'] = _wallet.added_time
        return response
#class transaksi log untuk ke mongo
class Ion_Point(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_point'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('ion_product_category.id'))
    amount = db.Column(db.Float)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _check(self, _id):
        response = {}
        debit = 0
        credit = 0
        user = Ion_User.query.filter_by(id=_id).first()
        if user is not None:
            _point = Ion_Point.query.filter_by(user_id=user.id, status=True).all()
            for i in _point:
                if i.type_id == 1:
                    debit += i.amount
                elif i.type_id == 2:
                    credit += i.amount
        response = debit - credit
        return response

class Ion_Activity_Wallet(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_activity_wallet'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    wallet = db.relationship('Ion_Wallet', backref='activity_wallet', lazy='dynamic')
    _product_type = db.relationship('Ion_Product_Type', backref='activity_wallet', lazy='dynamic')

    def _data(seld, _id):
        response = {}
        _trx = Ion_Activity_Wallet.query.filter_by(id=_id, status=True).first()
        response['id'] = _trx.id
        response['name'] = _trx.name
        return response

    @staticmethod
    def _insert_data():
        values = ['Debit', 'Credit','Pending']
        for v in values:
            _type = Ion_Activity_Wallet()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

class Ion_Trx_Status(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_trx_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(10))
    name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    image_service = db.relationship('Ion_Image_Service', backref='trx_status', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"status_code" : "50", "name": "Gagal"},
            {"status_code" : "00", "name": "Success"},
            {"status_code" : "60", "name": "Pending"}
        ]
        for v in values:
            _status = Ion_Trx_Status()
            _status.status_code = v['status_code']
            _status.name = v['name']
            db.session.add(_status)
            db.session.commit()

class Ion_Image_Gallery(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_image_gallery'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    image_name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    _product_category = db.relationship('Ion_Product_Category', backref='Image_Gallery', lazy='dynamic')
    help_category = db.relationship('Ion_Help_Category', backref='Image_Gallery', lazy='dynamic')
    # vehicle_brand = db.relationship('Vehicle_Brand', backref='Image_Gallery', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"title" : "IONCASH", "image_name": "ion-cash.png"},
            {"title" : "Pulsa", "image_name": "pulsa.png"},
            {"title" : "Hotel", "image_name": "hotel.png"},
            {"title" : "Obu Transaction", "image_name": "obu.png"}
        ]
        for v in values:
            _img = Ion_Image_Gallery()
            _img.title = v['title']
            _img.image_name = v['image_name']
            db.session.add(_img)
            db.session.commit()

class Ion_Product_Category(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_product_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    provider_id = db.Column(db.Integer, db.ForeignKey('ion_provider.id'))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    point = db.relationship('Ion_Point', backref='ion_product_category', lazy='dynamic')
    _product_type = db.relationship('Ion_Product_Type', backref='ion_product_category', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "IONCASH", "image_id": 1},
            {"name" : "Pulsa", "image_id": 2},
            {"name" : "Hotel", "image_id": 3},
            {"name" : "Obu Transaction", "image_id": 4}
        ]
        for v in values:
            _cat = Ion_Product_Category()
            _cat.name = v['name']
            _cat.image_id = v['image_id']
            db.session.add(_cat)
            db.session.commit()

    def _list(self):
        response = []
        values = Ion_Product_Category.query.filter_by(status=True).all()
        for v in values:
            response.append({
                'id': v.id,
                'name': v.name,
                # 'image': v.image_id
            })
        return response

class Ion_Product_Type(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_product_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    category_id = db.Column(db.Integer, db.ForeignKey('ion_product_category.id'))
    activity_id = db.Column(db.Integer, db.ForeignKey('ion_activity_wallet.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = ['Send', 'Receive','Withdraw','Topup']
        for v in values:
            _type = Ion_Product_Type()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

class Ion_Provider(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_provider'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    image = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    _product_category = db.relationship('Ion_Product_Category', backref='Provider', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ['Ion']
        for v in values:
            provider = Ion_Provider()
            provider.name = v
            db.session.add(provider)
            db.session.commit()

class Ion_Province(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_province'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = ['DKI Jakarta','Jawa Barat','Jawa Tengah','Jawa Timur']
        for v in values:
            province = Ion_Province()
            province.name = v
            db.session.add(province)
            db.session.commit()

class Ion_City(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_city'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    province_id = db.Column(db.Integer, db.ForeignKey('ion_province.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "Jakarta Pusat", "province_id": 1},
            {"name" : "Jakarta Utara", "province_id": 1},
            {"name" : "Jakarta Selatan", "province_id": 1},
            {"name" : "Jakarta Timur", "province_id": 1},
            {"name" : "Jakarta Barat", "province_id": 1},
            {"name" : "Bekasi", "province_id": 2},
            {"name" : "Bogor", "province_id": 2}

        ]
        for v in values:
            city = Ion_City()
            city.name = v['name']
            city.province_id = v['province_id']
            db.session.add(city)
            db.session.commit()

class Ion_Kecamatan(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_kecamatan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    city_id = db.Column(db.Integer, db.ForeignKey('ion_city.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "Senen", "city_id": 1},
            {"name" : "Kelapa Gading", "city_id": 2},
            {"name" : "Tebet", "city_id": 3},
            {"name" : "Jatinegara", "city_id": 4},
            {"name" : "Grogol", "city_id": 5},
            {"name" : "Cibitung", "city_id": 6},
            {"name" : "Jonggol", "city_id": 7}
        ]
        for v in values:
            kecamatan = Ion_Kecamatan()
            kecamatan.name = v['name']
            kecamatan.city_id = v['city_id']
            db.session.add(kecamatan)
            db.session.commit()

class Ion_Kelurahan(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_kelurahan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('ion_kecamatan.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "Kwitang", "kecamatan_id": 1},
            {"name" : "Pegangsaan Dua", "kecamatan_id": 2},
            {"name" : "Tebet Barat", "kecamatan_id": 3},
            {"name" : "Kampung Melayu", "kecamatan_id": 4},
            {"name" : "Petamburan", "kecamatan_id": 5},
            {"name" : "Sukajaya", "kecamatan_id": 6},
            {"name" : "Cibodas", "kecamatan_id": 7}
        ]
        for v in values:
            kecamatan = Ion_Kelurahan()
            kecamatan.name = v['name']
            kecamatan.kecamatan_id = v['kecamatan_id']
            db.session.add(kecamatan)
            db.session.commit()

class Ion_Postal_Code(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_postal_code'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128))
    kelurahan_id = db.Column(db.Integer, db.ForeignKey('ion_kelurahan.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"code" : "10420", "kecamatan_id": 1},
            {"code" : "14250", "kecamatan_id": 2},
            {"code" : "12810", "kecamatan_id": 3},
            {"code" : "13320", "kecamatan_id": 4},
            {"code" : "11450", "kecamatan_id": 5},
            {"code" : "17520", "kecamatan_id": 6},
            {"code" : "16830", "kecamatan_id": 7}
        ]
        for v in values:
            postal_code = Ion_Postal_Code()
            postal_code.code = v['code']
            postal_code.kecamatan_id = v['kecamatan_id']
            db.session.add(postal_code)
            db.session.commit()

class Ion_Obu_Detail(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_obu_detail'
    id = db.Column(db.Integer, primary_key=True)
    obu_id = db.Column(db.Integer, db.ForeignKey('ion_obu_list.id'))
    plate_id = db.Column(db.String(64))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    vehicle_type_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_type.id'))
    vehicle_brand_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_brand.id'))
    vehicle_series_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_series.id'))
    vehicle_model_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_model.id'))
    vehicle_color_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_color.id'))
    plate_photo_front = db.Column(db.String(128))
    plate_photo_back = db.Column(db.String(128))
    vehicle_photo_front = db.Column(db.String(128))
    vehicle_photo_back = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _update_detail_registered(self, _obu_id, _user_id):
        response = {}
        _obu = Ion_Obu_Detail()
        _obu.obu_id =_obu_id
        _obu.user_id =_user_id
        db.session.add(_obu)
        db.session.commit()
        response = Ion_Obu_Detail()._data(_obu.id)
        return response

    def _insert(self, _obu_id, _plate_id, _user_id, _vh_type_id, _vh_brand_id, _vh_series_id, _vh_model_id, _vh_color_id, _pl_photo_front, _pl_photo_back, _vehicle_front, _vehicle_back):
        response = {}
        _obu = Ion_Obu_Detail()
        _obu.obu_id =_obu_id
        _obu.plate_id = _plate_id.upper()
        _obu.user_id =_user_id
        _obu.vehicle_type_id = _vh_type_id
        _obu.vehicle_brand_id = _vh_brand_id
        _obu.vehicle_series_id = _vh_series_id
        _obu.vehicle_model_id =_vh_model_id
        _obu.vehicle_color_id = _vh_color_id
        _obu.plate_photo_front = _pl_photo_front
        _obu.plate_photo_back = _pl_photo_back
        _obu.vehicle_photo_front = _vehicle_front
        _obu.vehicle_photo_back = _vehicle_back
        _obu.added_time = datetime.now()
        db.session.add(_obu)
        db.session.commit()
        response = Ion_Obu_Detail()._data(_obu.id)
        return response

    def _list(self, obu_id):
        response = []
        _obu = Ion_Obu_Detail.query.filter_by(obu_id=obu_id, status=True).order_by(Ion_Obu_Detail.added_time.desc()).all()
        for i in _obu:
            vehicle_type_name = None
            vehicle_brand_name = None
            vehicle_series_name = None
            vehicle_model_name = None
            vehicle_color_name = None
            if i.vehicle_type_id is not None:
                _type = Ion_Vehicle_Type.query.filter_by(id=i.vehicle_type_id, status=True).first()
                _model = Ion_Vehicle_Model.query.filter_by(id=i.vehicle_model_id, status=True).first()
                _brand = Ion_Vehicle_Brand.query.filter_by(id=i.vehicle_brand_id, status=True).first()
                _series = Ion_Vehicle_Series.query.filter_by(id=i.vehicle_series_id, status=True).first()
                _color = Ion_Vehicle_Color.query.filter_by(id=i.vehicle_color_id, status=True).first()
                vehicle_type_name = _type.name
                vehicle_brand_name = _brand.name
                vehicle_series_name = _series.name
                vehicle_model_name = _model.name
                vehicle_color_name = _color.name
            _obu_uid = Ion_Obu_List.query.filter_by(id=i.obu_id, status=True).first()
            response.append({
                'id': i.id,
                'obu_id': i.obu_id,
                'obu_uid': _obu_uid.obu_uid,
                'plate_id': i.plate_id,
                'user_id': i.user_id,
                'vehicle_type_name' : vehicle_type_name,
                'vehicle_brand_name' : vehicle_brand_name,
                'vehicle_series_name' : vehicle_series_name,
                'vehicle_model_name' : vehicle_model_name,
                'vehicle_color_name' : vehicle_color_name,
                'front_plate' : i.plate_photo_front,
                'back_plate' : i.plate_photo_back,
                'front_vehicle' : i.vehicle_photo_front,
                'back_vehicle' : i.vehicle_photo_back
            })
        return response

    def _data(self, obu_id):
        response = {}
        _obu = Ion_Obu_Detail.query.filter_by(obu_id=obu_id, status=True).first()
        _vehicle_type = Ion_Vehicle_Type.query.filter_by(id=_obu.vehicle_type_id, status=True).first()
        _vehicle_brand = Ion_Vehicle_Brand.query.filter_by(id=_obu.vehicle_brand_id, status=True).first()
        _vehicle_color = Ion_Vehicle_Color.query.filter_by(id=_obu.vehicle_color_id, status=True).first()
        _vehicle_series = Ion_Vehicle_Series.query.filter_by(id=_obu.vehicle_series_id, status=True).first()
        _vehicle_model = Ion_Vehicle_Model.query.filter_by(id=_obu.vehicle_model_id, status=True).first()

        if _obu is not None:
            response['id'] = _obu.id
            response['user_id'] = _obu.user_id
            response['obu_id'] = _obu.obu_id
            response['plate_id'] = _obu.plate_id
            response['vehicle_type_id'] = _obu.vehicle_type_id
            response['vehicle_type_name'] = _vehicle_type.name
            response['vehicle_brand_id'] = _obu.vehicle_brand_id
            response['vehicle_brand_name'] = _vehicle_brand.name
            response['vehicle_series_id'] = _obu.vehicle_series_id
            response['vehicle_series_name'] = _vehicle_series.name
            response['vehicle_model_id'] = _obu.vehicle_model_id
            response['vehicle_model_name'] = _vehicle_model.name
            response['vehicle_color_id'] = _obu.vehicle_color_id
            response['vehicle_color_name'] = _vehicle_color.name
            response['front_plate'] = 'https://devtestion.ion-network.id/api/obu/images/' + _obu.plate_photo_front
            response['back_plate'] = 'https://devtestion.ion-network.id/api/obu/images/' + _obu.plate_photo_back
            response['front_vehicle'] = 'https://devtestion.ion-network.id/api/obu/images/' + _obu.vehicle_photo_front
            response['back_vehicle'] = 'https://devtestion.ion-network.id/api/obu/images/' + _obu.vehicle_photo_back
        return response

    def _update(self, _id, _obu_id, _plate_id, _user_id, _vh_type_id, _vh_brand_id, _vh_series_id, _vh_model_id, _vh_color_id, _pl_photo_front, _pl_photo_back, _vehicle_front, _vehicle_back):
        response = {}
        _obu = Ion_Obu_Detail.query.filter_by(id=_id, status=True).first()
        _obu.obu_id = _obu_id
        _obu.plate_id = _plate_id.upper()
        _obu.user_id =_user_id
        _obu.vehicle_type_id = _vh_type_id
        _obu.vehicle_brand_id = _vh_brand_id
        _obu.vehicle_series_id = _vh_series_id
        _obu.vehicle_model_id =_vh_model_id
        _obu.vehicle_color_id = _vh_color_id
        _obu.plate_photo_front = _pl_photo_front
        _obu.plate_photo_back = _pl_photo_back
        _obu.vehicle_photo_front = _vehicle_front
        _obu.vehicle_photo_back = _vehicle_back
        _obu.added_time = datetime.now()
        db.session.add(_obu)
        db.session.commit()
        return response

    def _delete(self, _id):
        _delete_ = Ion_Obu_Detail.query.filter_by(id=_id, status=True).first()
        _delete_.status = False
        db.session.add(_delete_)
        db.session.commit()

class Ion_Obu_List(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_obu_list'
    id = db.Column(db.Integer, primary_key=True)
    obu_uid = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'), default=None)
    pin_hash = db.Column(db.String(128))
    use_count = db.Column(db.Integer, default=1)
    # expired_date =  db.Column(db.Date(), default=datetime.now())
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    #relationship
    obu_detail = db.relationship('Ion_Obu_Detail', backref='obu_list', lazy='dynamic')

    def _list_active(self, limit=25, page=0):
        response = []
        page = page * limit
        user = db.session.query(db.func.max(Ion_Obu_List.use_count), Ion_Obu_List.obu_uid).group_by(Ion_Obu_List.obu_uid).filter(Ion_Obu_List.user_id == None).filter_by(status=True).offset(page).limit(limit).all()
        # user = Ion_Obu_List.query.filter(Ion_Obu_List.user_id == None).filter_by(status=True).offset(page).limit(limit).all()
        for u in user:
            obu_id = Ion_Obu_List.query.filter(Ion_Obu_List.obu_uid == u[1]).filter(Ion_Obu_List.use_count == u[0]).first()
            response.append({
                'id': obu_id.id,
                'uid': obu_id.obu_uid,
                'user': Ion_User()._data(obu_id.user_id),
            })
        return response

    def _list_all(self, limit=25, page=0):
        response = []
        page = page * limit
        user = db.session.query(db.func.max(Ion_Obu_List.use_count), Ion_Obu_List.obu_uid).group_by(Ion_Obu_List.obu_uid).offset(page).limit(limit).all()
        for u in user:
            obu_id = Ion_Obu_List.query.filter(Ion_Obu_List.obu_uid == u[1]).filter(Ion_Obu_List.use_count == u[0]).first()
            response.append({
                'id': obu_id.id,
                'uid': obu_id.obu_uid,
                'user': Ion_User()._data(obu_id.user_id),
            })
        return response

    def _list_by_user(self, limit=25, page=0):
        response = []
        page = page * limit
        user = db.session.query(db.func.max(Ion_Obu_List.use_count), Ion_Obu_List.obu_uid).group_by(Ion_Obu_List.obu_uid).filter(Ion_Obu_List.user_id != None).offset(page).limit(limit).all()
        for u in user:
            obu_id = Ion_Obu_List.query.filter(Ion_Obu_List.obu_uid == u[1]).filter(Ion_Obu_List.use_count == u[0]).first()
            response.append({
                'id': obu_id.id,
                'uid': obu_id.obu_uid,
                'user': Ion_User()._data(obu_id.user_id),
            })
        return response

    def _list_nonactive(self, limit=25, page=0):
        response = []
        page = page * limit
        user = db.session.query(db.func.max(Ion_Obu_List.use_count), Ion_Obu_List.obu_uid).group_by(Ion_Obu_List.obu_uid).filter(Ion_Obu_List.user_id == None).filter_by(status=False).offset(page).limit(limit).all()
        for u in user:
            obu_id = Ion_Obu_List.query.filter(Ion_Obu_List.obu_uid == u[1]).filter(Ion_Obu_List.use_count == u[0]).first()
            response.append({
                'id': obu_id.id,
                'uid': obu_id.obu_uid,
                'user': Ion_User()._data(obu_id.user_id),
            })
        return response

    def _count(self):
        response = {}
        response['total_obu'] = db.session.query(db.func.max(Ion_Obu_List.use_count), Ion_Obu_List.obu_uid).group_by(Ion_Obu_List.obu_uid).count()
        response ['user_owned'] = db.session.query(db.func.max(Ion_Obu_List.use_count), Ion_Obu_List.obu_uid).group_by(Ion_Obu_List.obu_uid).filter(Ion_Obu_List.user_id != None).count()
        response['non_active_obu'] = Ion_Obu_List.query.filter(Ion_Obu_List.user_id == None).filter_by(status=False).count()
        response ['active_obu'] = Ion_Obu_List.query.filter(Ion_Obu_List.user_id == None).filter_by(status=True).count()
        return response

    def _data(self, obu_id): #untuk membaca data user kebutuhan transaksi
        response = {}
        obu = Ion_Obu_List.query.filter_by(id=obu_id, status=True).first()
        user = Ion_User.query.filter_by(id=obu.user_id).first()
        total_obu = Ion_Obu_List.query.filter_by(id=obu_id, status=True).count()
        # wallet= Ion_Wallet.query.filter_by(user_id=obu.user_id).first()._check()
        response['user_id'] = user.id
        response['phone'] = user.phone_number
        response['name'] = user.name
        response['email'] = user.email
        response['wallet'] = Ion_Wallet()._check(obu.user_id)
        response['total_obu'] = total_obu
        # response['referral'] = user.referral
        return response
    @property
    def pin(self):
        raise AttributeError('pin is not a readable attribute')

    @pin.setter
    def pin(self, pin):
        self.pin_hash = generate_password_hash(pin)

    def verify_pin(self, pin):
        return check_password_hash(self.pin_hash, pin)

    def _insert(self, _obu_uid, _pin):
        _obu_list_ = Ion_Obu_List()
        _obu_list_.obu_uid = _obu_uid
        _obu_list_.pin = _pin
        db.session.add(_obu_list_)
        db.session.commit()

    def _insert_new(self, _obu_uid, _pin, _lastcount):
        _obu_list_ = Ion_Obu_List()
        _obu_list_.obu_uid = _obu_uid
        _obu_list_.pin = _pin
        _obu_list_.use_count = _lastcount
        db.session.add(_obu_list_)
        db.session.commit()

    def _data2(self, _obu_uid):
        response = {}
        _read_count = Ion_Obu_List.query.filter_by(id=_obu_uid)
        response['count'] = _read_count.use_count
        return response

    def _update_owner(self, _id, _user_id, _obu_uid):
        _check_row = Ion_Obu_List.query.filter_by(obu_uid=_obu_uid).all() #lihat semua row dengan uid untuk melakukan cek use count
        _read_count = Ion_Obu_List.query.filter_by(id=_id, status=True).first() #untuk membaca use count terahir yang akan dipakai

        #OBU sudah pernah digunakan oleh orang lain untuk use count +1
        if len(_check_row) > 1:
            _counter = int(_read_count.use_count) + 1
            _update_owner = Ion_Obu_List.query.filter_by(id=_id).first()
            _update_owner.user_id = _user_id
            _update_owner.use_count = _counter
            _update_owner.status = True
            db.session.add(_update_owner)
            db.session.commit()

        #OBU baru diaktifkan dan digunakan
        else:
            _update_owner = Ion_Obu_List.query.filter_by(id=_id).first()
            _update_owner.user_id = _user_id
            _update_owner.status = True
            db.session.add(_update_owner)
            db.session.commit()

    def _delete(self, _obu_uid):
        _update_status = Ion_Obu_List.query.filter_by(id=_obu_uid).first()
        _update_status.status = False
        db.session.add(_update_status)
        db.session.commit()

    @staticmethod
    def _insert_data():
        values = [
            {"obu_uid" : "A123456", "pin_hash": "123456"},
            {"obu_uid" : "B121212", "pin_hash": "121212"},
            {"obu_uid" : "C131313", "pin_hash": "131313"}
        ]
        for v in values:
            _list = Ion_Obu_List()
            _list.obu_uid = v['obu_uid']
            _list.pin = v['pin_hash']
            db.session.add(_list)
            db.session.commit()

class Ion_Plate_Expired(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_plate_expired'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'), default=None)
    plate_id = db.Column(db.String(64))
    obu_id = db.Column(db.Integer, db.ForeignKey('ion_obu_list.id'))
    expired_month =  db.Column(db.Integer)
    expired_year = db.Column(db.Integer)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _obu_id, _plate_id, _user_id, _month, _year):
        response = {}
        _expired = Ion_Obu_Detail()
        _expired.user_id =_obu_id
        _expired.plate_id = _plate_id
        _expired.user_id =_user_id
        _expired.obu_id = _obu_id
        _expired.expired_month = _month
        _expired.expired_year = _year
        db.session.add(_expired)
        db.session.commit()
        return response

    def _delete(self, _id):
        _update_status = Ion_Plate_Expired.query.filter_by(id=_id).first()
        _update_status.status = False
        db.session.add(_update_status)
        db.session.commit()

class Ion_Vehicle_Type(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_vehicle_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    #relationship
    vehicle_brand = db.relationship('Ion_Vehicle_Brand', backref='Vehicle_Type', lazy='dynamic')
    obu_detail = db.relationship('Ion_Obu_Detail', backref='Vehicle_Type', lazy='dynamic')

    def _list(self):
        response = {}
        response = []
        _type = Ion_Vehicle_Type.query.filter_by(status=True).all()
        for i in _type:
            response.append({
                'id': i.id,
                'type': i.name
            })
        return response

    @staticmethod
    def _insert_data():
        values = ["Motorcycle","Car"]
        for v in values:
            _type = Ion_Vehicle_Type()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

class Ion_Vehicle_Model(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_vehicle_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    vehicle_series = db.relationship('Ion_Vehicle_Series', backref='Vehicle_Model', lazy='dynamic')
    obu_detail = db.relationship('Ion_Obu_Detail', backref='Vehicle_Model', lazy='dynamic')

    def _data(self):
        response = {}
        _type = Ion_Vehicle_Model.query.filter_by(status=True).first()
        response['name'] = _type.name
        return response

    def _list(self):
        response = {}
        response = []
        _model = Vehicle_Model.query.filter_by(status=True).all()
        for i in _model:
            response.append({
                'id': i.id,
                'model': i.name
            })
        return response

    @staticmethod
    def _insert_data():
        values = ["CUB","Matic","Sport","OffRoad","MPV","Sedan","SUV"]
        for v in values:
            _model = Ion_Vehicle_Model()
            _model.name = v
            db.session.add(_model)
            db.session.commit()

class Ion_Vehicle_Brand(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_vehicle_brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    type_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_type.id'))
    # image_id = db.Column(db.Integer, db.ForeignKey('image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    vehicle_series = db.relationship('Ion_Vehicle_Series', backref='Vehicle_Brand', lazy='dynamic')
    obu_detail = db.relationship('Ion_Obu_Detail', backref='Vehicle_Brand', lazy='dynamic')

    def _data(self):
        response = {}
        _model = Ion_Vehicle_Brand.query.filter_by(status=True).first()
        response['name'] = _model.name
        response['type_id'] = _model.type_id
        return response

    def _list(self):
        response = {}
        response = []
        _brand = Ion_Vehicle_Brand.query.filter_by(status=True).all()
        for i in _brand:
            response.append({
                'id': i.id,
                'brand': i.name,
                'type_id': i.type_id
            })
        return response

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "Suzuki", "type_id": 1},
            {"name" : "Suzuki", "type_id": 2},
            {"name" : "Honda", "type_id": 1},
            {"name" : "Honda", "type_id": 2}
        ]
        for v in values:
            brand = Ion_Vehicle_Brand()
            brand.name = v['name']
            brand.type_id = v['type_id']
            db.session.add(brand)
            db.session.commit()

class Ion_Vehicle_Series(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_vehicle_series'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    brand_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_brand.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_type.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_model.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    obu_detail = db.relationship('Ion_Obu_Detail', backref='Vehicle_Series', lazy='dynamic')

    def _data(self):
        response = {}
        _series = Ion_Vehicle_Series.query.filter_by(status=True).first()
        response['name'] = _series.name
        response['brand_id'] = _series.brand_id
        response['model_id'] = _series.model_id
        return response

    def _list(self):
        response = {}
        response = []
        _series = Ion_Vehicle_Series.query.filter_by(status=True).all()
        for i in _series:
            response.append({
                'id': i.id,
                'name': i.name,
                'brand_id': i.brand_id,
                'type_id': i.type_id,
                'model_id': i.model_id
            })
        return response

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "Smash", "brand_id": 1, "type_id": 1, "model_id": 1},
            {"name" : "APV", "brand_id": 2, "type_id": 2, "model_id": 5},
            {"name" : "Beat", "brand_id": 3, "type_id": 1, "model_id": 2},
            {"name" : "CR-V", "brand_id": 4, "type_id": 2, "model_id": 7}

        ]
        for v in values:
            series = Ion_Vehicle_Series()
            series.name = v['name']
            series.brand_id = v['brand_id']
            series.type_id = v['type_id']
            series.model_id = v['model_id']
            db.session.add(series)
            db.session.commit()

class Ion_Vehicle_Color(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_vehicle_color'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    obu_detail = db.relationship('Ion_Obu_Detail', backref='Vehicle_Color', lazy='dynamic')

    def _data(self):
        response = {}
        _color = Ion_Vehicle_Color.query.filter_by(status=True).first()
        response['color'] = _color.name
        return response

    def _list(self):
        response = {}
        response= []
        _color = Ion_Vehicle_Color.query.filter_by(status=True).all()
        for i in _color:
            response.append({
                'id': i.id,
                'color': i.name
            })
        return response

    @staticmethod
    def _insert_data():
        values = ["Black", "White", "Silver", "Red", "Green", "Yellow", "Blue"]
        for v in values:
            color = Ion_Vehicle_Color()
            color.name = v
            db.session.add(color)
            db.session.commit()

class Ion_Messages(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_messages'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(128))
    content = db.Column(db.String(255))
    image = db.Column(db.String(255))
    # product_category_id = db.Column(db.Integer, db.ForeignKey('_product_category.id'))
    link = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _user_id, _subject, _content, _image, _link):
        MSG_IMG = join(dirname(realpath(__file__)), '../images/messages')
        apps.config['MSG_IMG'] = MSG_IMG
        cur_user = Ion_User.query.filter_by(id=_user_id).first()
        msg, msg_ext = os.path.splitext(_image.filename)
        _img = str(cur_user.id)+'#'+str(time.time()).replace('.', '')+msg_ext
        _image.save(os.path.join(apps.config['MSG_IMG'], _img))
        _messages = Ion_Messages()
        _messages.subject= _subject
        _messages.content= _content
        _messages.image= _img
        _messages.link= _link
        db.session.add(_messages)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _messages = Ion_Messages.query.order_by(Ion_Messages.id.desc()).all()
        for i in _messages:
            response['data'].append({
                'id': i.id,
                'subject': i.subject,
                'content': i.content,
                'image': i.image,
                'link': i.link,
                'day': i.added_time.strftime("%a"),
                'date': i.added_time.day,
                'month': i.added_time.strftime("%b"),
                'year': i.added_time.year,
                'time': str(i.added_time.hour)+":"+str(i.added_time.minute)
            })
        return response

    def _data(self, _id):
        response = {}
        _message = Ion_Messages.query.filter_by(id=_id, status=True).first()
        response['subject'] = _message.subject
        response['content'] = _message.content
        response['image'] = _message.image
        response['link'] = _message.link
        response['time'] = _message.added_time
        return response

class Ion_Image_Service(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_image_service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    image_title_id = db.Column(db.Integer, db.ForeignKey('ion_image_title.id'))
    verification_id = db.Column(db.Integer, db.ForeignKey('ion_trx_status.id'), default=2)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    updated_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _name, _user_id, _img_title_id):
        _img_service_ = Ion_Image_Service()
        _img_service_.name = _name
        _img_service_.user_id = _user_id
        _img_service_.image_title_id = _img_title_id
        db.session.add(_img_service_)
        db.session.commit()

    def _verify(self, _user_id):
        _verify = Ion_Image_Service.query.filter_by(user_id=_user_id).all()
        _verify.verification = True
        db.session.add(_verify)
        db.session.commit()

class Ion_Image_Title(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_image_title'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    image_service = db.relationship('Ion_Image_Service', backref='Image_Title', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ["Front plate", "Back Plate", "Front Vehicle", "Back Vehicle", "Id Card", "profile Photo", "Selfie Id Card", "Messages"]
        for v in values:
            img = Ion_Image_Title()
            img.name = v
            db.session.add(img)
            db.session.commit()

class Ion_Transaction_Type(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_transaction_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    topup_detail = db.relationship('Ion_Topup_List', backref='Transaction_Type', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ["Offline", "Online"]
        for v in values:
            _type = Ion_Transaction_Type()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

class Ion_Topup_List(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_topup_list'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    transaction_type = db.Column(db.Integer, db.ForeignKey('ion_transaction_type.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    topup_detail = db.relationship('Ion_Topup_Detail', backref='Topup_List', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"title" : "Pojok Halal", "image_id": 1, "transaction_type" : 1},
            {"title" : "BCA", "image_id": 1, "transaction_type" : 2},
            {"title" : "Mandiri", "image_id": 1, "transaction_type" : 2},
            {"title" : "Indomart", "image_id": 1, "transaction_type" : 1}
        ]
        for v in values:
            _list = Ion_Topup_List()
            _list.title = v['title']
            _list.image_id = v['image_id']
            _list.transaction_type = v['transaction_type']
            db.session.add(_list)
            db.session.commit()

    def _list(self):
        response = {}
        response = []
        _topup = Ion_Topup_List.query.filter_by(status=True).all()
        for i in _topup:
            response.append({
                'id': i.id,
                'title': i.title,
                'image_id': i.image_id,
                'transaction_type': i.transaction_type
            })
        return response

class Ion_Topup_Detail(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_topup_detail'
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('ion_topup_list.id'))
    title = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    topup_description = db.relationship('Ion_Topup_Description', backref='Topup_Detail', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"list_id" : 1, "title": "Datang Langsung ke Pojok Halal"},
            {"list_id" : 2, "title": "Lewat ATM BCA"},
            {"list_id" : 3, "title": "Lewat ATM Mandiri"},
            {"list_id" : 4, "title": "Lewat Chasier Indomart"}
        ]
        for v in values:
            _detail = Ion_Topup_Detail()
            _detail.list_id = v['list_id']
            _detail.title = v['title']
            db.session.add(_detail)
            db.session.commit()

    def _list(self):
        response = {}
        response = []
        _topup = Ion_Topup_Detail.query.filter_by(status=True).all()
        for i in _topup:
            response.append({
                'id': i.id,
                'list_id': i.list_id,
                'title': i.title
            })
        return response

class Ion_Topup_Description(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_topup_description'
    id = db.Column(db.Integer, primary_key=True)
    detail_id = db.Column(db.Integer, db.ForeignKey('ion_topup_detail.id'))
    description = db.Column(db.String(255))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"detail_id" : 1, "description": "detail 1 point 1"},
            {"detail_id" : 1, "description": "detail 1 point 2"},
            {"detail_id" : 2, "description": "detail 2 point 1"},
            {"detail_id" : 2, "description": "detail 2 point 2"}
        ]
        for v in values:
            _description = Ion_Topup_Description()
            _description.detail_id = v['detail_id']
            _description.description = v['description']
            db.session.add(_description)
            db.session.commit()

    def _list(self):
        response = {}
        response = []
        _topup = Ion_Topup_Description.query.filter_by(status=True).all()
        for i in _topup:
            response.append({
                'id': i.id,
                'detail_id': i.detail_id,
                'description': i.description
            })
        return response

class Ion_Privacy_Policy(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_privacy_policy'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"title": "Privacy 1", "description" : "Privacy 1 explained"},
            {"title": "Privacy 2", "description" : "Privacy 2 explained"}
        ]
        for v in values:
            _privacy = Ion_Privacy_Policy()
            _privacy.title = v['title']
            _privacy.description = v['description']
            db.session.add(_privacy)
            db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _policy = Ion_Privacy_Policy.query.order_by(Privacy_Policy.id.desc()).all()
        for i in _policy:
            response['data'].append({
                'id': i.id,
                'title': i.title,
                'description': i.description
            })
        return response

class Ion_Term_Of_Service(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_term_of_service'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"title": "Term Of use", "description" : "Term of Use explained"}
        ]
        for v in values:
            _term = Ion_Term_Of_Service()
            _term.title = v['title']
            _term.description = v['description']
            db.session.add(_term)
            db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _policy = Ion_Privacy_Policy.query.order_by(Privacy_Policy.id.desc()).all()
        for i in _policy:
            response['data'].append({
                'id': i.id,
                'title': i.title,
                'description': i.description
            })
        return response

    def _data(self, _id):
        response = {}
        _message = Ion_Term_Of_Service.query.filter_by(id=_id, status=True).first()
        response['id'] = _message.id
        response['title'] = _message.title
        response['description'] = _message.description
        return response

class Ion_Help_Category(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_help_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(125))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    help = db.relationship('Ion_Help', backref='Help_Category', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ["ION CASH", "OBU", "PULSA"]
        for v in values:
            _help = Ion_Help_Category()
            _help.name = v
            db.session.add(_help)
            db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _help = Ion_Help_Category.query.order_by(Help_Category.id.desc()).all()
        for i in _help:
            response['data'].append({
                'id': i.id,
                'name': i.name,
                'image_id': i.image_id
            })
        return response

class Ion_Help(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_help'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('ion_help_category.id'))
    title = db.Column(db.String(64))
    description = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    @staticmethod
    def _insert_data():
        values = [
            {"category_id" : 1, "title" : "Pembayaran dengan ion cash", "description" : "Anda bisa melakukan pembayaran dengan menggunakan ion cash di setiap outlet yang terdaftar"},
            {"category_id" : 1, "title" : "Apa itu OBU", "description" : "OBU adalah suatu alat untuk pembacaan di mobil"},
            {"category_id" : 3, "title" : "Pulsa", "description" : "Pulsa bisa di topup di manapun kapanpun"}
        ]
        for v in values:
            help = Ion_Help()
            help.category_id = v['category_id']
            help.title = v['title']
            help.description = v['description']
            db.session.add(help)
            db.session.commit()

    def _list(self):
        response = {}
        response = []
        _help = Ion_Help.query.filter_by(status=True).all()
        for i in _help:
            response.append({
                'id': i.id,
                'category_id': i.category_id,
                'title': i.title,
                'description': i.description
            })
        return response

class Ion_Activity_Type(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_activity_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    log_activity = db.relationship('Ion_Log_Activity', backref='Activity_Type', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ["Register", "Login", "Transfer Money", "Topup", "History"]
        for v in values:
            _type = Ion_Activity_Type()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

class Ion_Log_Activity(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_log_activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    activity_type_id =  db.Column(db.Integer, db.ForeignKey('ion_activity_type.id'))
    ip_address = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Inbox(db.Model):
    __bind_key__ = 'users'
    __tablename__ = 'ion_inbox'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(128))
    content = db.Column(db.String(255))
    image = db.Column(db.String(255))
    icon_image = db.Column(db.String(255))
    product_category_id = db.Column(db.Integer, db.ForeignKey('ion_product_category.id'))
    link = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _subject, _content, _icon_image, _link, _prod_cat_id, _image):
        _inbox = Inbox()
        _inbox.subject= _subject
        _inbox.content= _content
        _inbox.icon_image= _icon_image
        _inbox.link= _link
        _inbox.product_category_id= _prod_cat_id
        _inbox.image= _image
        db.session.add(_inbox)
        db.session.commit()

    def _list(self,limit=25, page=0):
        response = []
        page = page * limit
        _inbox = Inbox.query.filter_by(status=True).order_by(Inbox.added_time.desc()).all()
        for i in _inbox:
            response.append({
                'id': i.id,
                'subject': i.subject,
                'content': i.content,
                'image': i.image,
                'product_cat': i.product_category_id,
                'link': i.link,
                'day': i.added_time.strftime("%a"),
                'date': i.added_time.day,
                'month': i.added_time.strftime("%b"),
                'year': i.added_time.year,
                'time': str(i.added_time.strftime("%H"))+":"+str(i.added_time.strftime("%M"))
            })
        return response

    def _trash_list(self,limit=25, page=0):
        response = []
        page = page * limit
        _inbox = Inbox.query.filter_by(status=False).order_by(Inbox.added_time.desc()).all()
        for i in _inbox:
            response.append({
                'id': i.id,
                'subject': i.subject,
                'content': i.content,
                'image': i.image,
                'link': i.link,
                'day': i.added_time.strftime("%a"),
                'date': i.added_time.day,
                'month': i.added_time.strftime("%b"),
                'year': i.added_time.year,
                'time': str(i.added_time.strftime("%H"))+":"+str(i.added_time.strftime("%M"))
            })
        return response

    def _delete(self, _id):
        _inbox = Inbox.query.filter_by(id=_id).first()
        _inbox.status = False
        db.session.add(_inbox)
        db.session.commit()

    def _inbox_list(self, _user_id):
        response = {}
        response['data'] = []
        _inbox = Inbox.query.order_by(Inbox.added_time.desc()).all()
        for i in _inbox:
            response['data'].append({
                'id': i.id,
                'subject': i.subject,
                'content': i.content,
                'image': i.image,
                'icon_image': i.icon_image,
                'link': i.link,
                'added_time': i.added_time,
                'day': i.added_time.strftime("%a"),
                'date': i.added_time.day,
                'month': i.added_time.strftime("%b"),
                'year': i.added_time.year,
                'time': str(i.added_time.strftime("%H"))+":"+str(i.added_time.strftime("%M"))
            })
        _request = Ion_Request.query.filter_by(to_user_id=_user_id, status=True).order_by(Ion_Request.added_time.desc()).all()
        for s in _request:
            _user = Ion_User.query.filter_by(id=s.from_user_id).first()
            _trx_status = Ion_Trx_Status.query.filter_by(id=s.trx_status).first()
            response['data'].append({
                'id': s.id,
                'subject': s.subject,
                'description': s.description,
                'amount': s.amount,
                'icon_image': s.icon_image,
                'from_user_id': s.from_user_id,
                'from_user_name': _user.name,
                'from_user_email': _user.email,
                'from_user_phone': _user.phone_number,
                'to_user_id': s.to_user_id,
                'trx_status': _trx_status.status_code,
                'added_time': s.added_time,
                'day': s.added_time.strftime("%a"),
                'date': s.added_time.day,
                'month': s.added_time.strftime("%b"),
                'year': s.added_time.year,
                'time': str(s.added_time.strftime("%H"))+":"+str(s.added_time.strftime("%M"))
            })

    def _count(self):
        response = {}
        response['total_message'] = Inbox.query.filter_by(status=True).count()
        response['total_trash'] = Inbox.query.filter_by(status=False).count()
        return response

class Ion_Inbox_Upgrade(db.Model):
    __bind_key__='users'
    __tablename__ = 'ion_inbox_upgrade'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(128))
    content = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    icon_image = db.Column(db.String(255))
    product_category_id = db.Column(db.Integer, db.ForeignKey('ion_product_category.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _subject, _content, _user_id, _icon_image):
        _inbox_req = Ion_Inbox_Upgrade()
        _inbox_req.subject= _subject
        _inbox_req.content= _content
        _inbox_req.user_id= _user_id
        _inbox_req.icon_image= _icon_image
        _inbox_req.added_time = datetime.now()
        db.session.add(_inbox_req)
        db.session.commit()

class Ion_Notification_Type(db.Model):
    __bind_key__='users'
    __tablename__ = 'ion_notification_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(74))
    page = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    notification = db.relationship('Ion_Notification', backref='Notification_Type', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "Transaction", "page": "history"},
            {"name" : "Inbox", "page": "inbox"}
        ]
        for v in values:
            _type = Ion_Notification_Type()
            _type.name = v['name']
            _type.page = v['page']
            db.session.add(_type)
            db.session.commit()

class Ion_Notification(db.Model):
    __bind_key__='users'
    __tablename__ = 'ion_notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    notification_type = db.Column(db.Integer, db.ForeignKey('ion_notification_type.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _user_id, _notif_type):
        _notif = Ion_Notification()
        _notif.user_id = _user_id
        _notif.notification_type = _notif_type
        db.session.add(_notif)
        db.session.commit()

    def _notif_readed(self, _user_id, _notify):
        if _notify == 'history':
            _notif = Notification.query.filter_by(user_id=_user_id, notification_type=1).all()
            for i in _notif:
                i.status = False
                db.session.add(i)
                db.session.commit()
        elif _notify == 'inbox':
            _notif = Notification.query.filter_by(user_id=_user_id, notification_type=2).all()
            for i in _notif:
                i.status = False
                db.session.add(i)
                db.session.commit()

class Ion_Status_Upgrade(db.Model):
    __bind_key__='users'
    __tablename__ = 'ion_status_upgrade'
    id = db.Column(db.Integer, primary_key=True)
    status_upgrade = db.Column(db.Integer)
    description = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    upgrade = db.relationship('Ion_Upgrade', backref='Status_Upgrade', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"status_upgrade" : 0,"description": "Pending"},
            {"status_upgrade" : 1,"description": "Accept"},
            {"status_upgrade" : 2,"description": "Reject"}
        ]
        for v in values:
            _st_upgrade = Status_Upgrade()
            _st_upgrade.status_upgrade = v['status_upgrade']
            _st_upgrade.description = v['description']
            db.session.add(_st_upgrade)
            db.session.commit()

class Ion_Upgrade(db.Model):
    __bind_key__='users'
    __tablename__ = 'ion_upgrade'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    id_card = db.Column(db.String(128))
    id_card_type_image = db.Column(db.Integer)
    selfie_photo = db.Column(db.String(128))
    status_upgrade_id = db.Column(db.Integer, db.ForeignKey('ion_status_upgrade.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _user_id, _id_card, _id_card_type_image):
        _upgrade = Upgrade()
        _upgrade.user_id = _user_id
        _upgrade.id_card = _id_card
        _upgrade.id_card_type_image = _id_card_type_image
        _upgrade.status = False
        _upgrade.status_upgrade_id = 1
        db.session.add(_upgrade)
        db.session.commit()
        response = Upgrade()._data(_upgrade.id)
        return response

    def _data(self, id_upgrade):
        response = {}
        _upgrade = Ion_Upgrade.query.filter_by(id=id_upgrade, status=True).first()
        _status = Ion_Status_Upgrade.query.filter_by(id=_upgrade.status_upgrade_id, status=True).first()
        response['id'] = id_upgrade
        response['user_id'] = _upgrade.user_id
        response['status_upgrade'] = _status.description
        response['id_card'] = 'https://devtestion.ion-network.id/api/v1/auth/verification-images/' + _upgrade.id_card
        response['selfie_photo'] = 'https://devtestion.ion-network.id/api/v1/auth/verification-images/' + _upgrade.selfie_photo
        return response

    def _update_id_card(self, _user_id, _id_card, _id_card_type_image):
        _upgrade = Ion_Upgrade.query.filter_by(user_id=_user_id).order_by(Ion_Upgrade.id.desc()).first()
        _upgrade.user_id = _user_id
        _upgrade.id_card = _id_card
        _upgrade.id_card_type_image = _id_card_type_image
        db.session.add(_upgrade)
        db.session.commit()

    def _update_selfie_id(self, _user_id, _selfie_photo):
        _upgrade = Ion_Upgrade.query.filter_by(user_id=_user_id).order_by(Ion_Upgrade.id.desc()).first()
        _upgrade.user_id = _user_id
        _upgrade.selfie_photo = _selfie_photo
        db.session.add(_upgrade)
        db.session.commit()

    def _upgrade_account(self, _user_id, _status_upgrade):
        _upgrade = Ion_Upgrade.query.filter_by(user_id=_user_id).order_by(Ion_Upgrade.id.desc()).first()
        _upgrade.status_upgrade_id = _status_upgrade #pending
        _upgrade.status = True
        db.session.add(_upgrade)
        db.session.commit()

    def _list_upgraded(self, limit=25, page=0):
        response = []
        page = page * limit
        upgraded = Ion_Upgrade.query.filter(Ion_User.id_upgrade != None).filter_by(status=True).filter(Ion_Upgrade.status_upgrade_id == 2).order_by(Ion_Upgrade.user_id.asc()).offset(page).limit(limit).all()
        for u in upgraded:
            user = Ion_User.query.filter_by(id=u.user_id).first()
            response.append({
                'id': user.id,
                'name': user.name,
                'phone_number': user.phone_number,
                'email': user.email if user.email != None else '-',
                'wallet': Ion_Wallet()._check(user.id),
                'added_time': user.added_time.year,
                'id_upgrade': user.id_upgrade
            })
        return response

    def _list_request_upgrade(self, limit=25, page=0):
        response = []
        page = page * limit
        upgraded = Ion_Upgrade.query.filter(Ion_User.id_upgrade != None).filter_by(status=True).filter(Ion_Upgrade.status_upgrade_id == 1).order_by(Ion_Upgrade.user_id.asc()).offset(page).limit(limit).all()
        for u in upgraded:
            user = Ion_User.query.filter_by(id=u.user_id).first()
            response.append({
                'id': user.id,
                'name': user.name,
                'phone_number': user.phone_number,
                'email': user.email if user.email != None else '-',
                'wallet': Ion_Wallet()._check(user.id),
                'added_time': user.added_time.year,
                'id_upgrade': user.id_upgrade
            })
        return response

class Ion_Request(db.Model):
    __bind_key__='users'
    __tablename__ = 'ion_request'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(128))
    description = db.Column(db.String(255))
    amount = db.Column(db.Integer)
    icon_image = db.Column(db.String(255))
    product_category_id = db.Column(db.Integer, db.ForeignKey('ion_product_category.id'))
    from_user_id = db.Column(db.Integer)
    to_user_id = db.Column(db.Integer)
    trx_status = db.Column(db.Integer, db.ForeignKey('ion_trx_status.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _subject, _description, _amount, _icon_image, _prod_cat_id, _from_user_id, _to_user_id, _trx_status):
        _request = Ion_Request()
        _request.subject = _subject
        _request.description = _description
        _request.amount = _amount
        _request.icon_image= _icon_image
        _request.product_category_id= _prod_cat_id
        _request.from_user_id = _from_user_id
        _request.to_user_id = _to_user_id
        _request.trx_status = _trx_status
        _request.added_time = datetime.now()
        db.session.add(_request)
        db.session.commit()

    def _inbox_list(self, _user_id):
        response = {}
        response['data'] = []
        _request = Ion_Request.query.filter_by(to_user_id=_user_id, status=False).order_by(Ion_Request.added_time.desc()).all()
        for s in _request:
            _user = Ion_User.query.filter_by(id=s.from_user_id).first()
            _trx_status = Ion_Trx_Status.query.filter_by(id=s.trx_status).first()
            response['data'].append({
                'id': s.id,
                'subject': s.subject,
                'description': s.description,
                'amount': s.amount,
                'icon_image': s.icon_image,
                'from_user_id': s.from_user_id,
                'from_user_name': _user.name,
                'from_user_email': _user.email,
                'from_user_phone': _user.phone_number,
                'to_user_id': s.to_user_id,
                'trx_status': _trx_status.status_code,
                'added_time': s.added_time,
                'day': s.added_time.strftime("%a"),
                'date': s.added_time.day,
                'month': s.added_time.strftime("%b"),
                'year': s.added_time.year,
                'time': str(s.added_time.strftime("%H"))+":"+str(s.added_time.strftime("%M"))
            })

    def _list(self, limit=25, page=0):
        response = []
        page = page * limit
        _request = Ion_Request.query.order_by(Ion_Request.added_time.desc()).all()
        for s in _request:
            _from_user = Ion_User.query.filter_by(id=s.from_user_id).first()
            _to_user = Ion_User.query.filter_by(id=s.to_user_id).first()
            _trx_status = Ion_Trx_Status.query.filter_by(id=s.trx_status).first()
            response.append({
                'id': s.id,
                'subject': s.subject,
                'description': s.description,
                'amount': s.amount,
                'icon_image': s.icon_image,
                'from_user_id': s.from_user_id,
                'from_user_name': _from_user.name,
                'from_user_email': _from_user.email,
                'from_user_phone': _from_user.phone_number,
                'to_user_id': s.to_user_id,
                'to_user_name': _to_user.name,
                'to_user_email': _to_user.email,
                'to_user_phone': _to_user.phone_number,
                'trx_status': _trx_status.name,
                'added_time': s.added_time,
                'day': s.added_time.strftime("%a"),
                'date': s.added_time.day,
                'month': s.added_time.strftime("%b"),
                'year': s.added_time.year,
                'time': str(s.added_time.strftime("%H"))+":"+str(s.added_time.strftime("%M"))
            })
        return response

    def _data(self, _id):
        response = {}
        _request = Ion_Request.query.filter_by(id=_id, status=True).first()
        response['subject'] = _request.subject
        response['description'] = _request.description
        response['amount'] = _request.amount
        response['icon_image'] = _request.icon_image
        response['from_user_id'] = _request.from_user_id
        response['to_user_id'] = _request.to_user_id
        response['trx_status'] = _request.trx_status
        response['time'] = _request.added_time
        return response

    def _update(self, _id, _trx_status):
        _request = Ion_Request.query.filter_by(id=_id).first()
        _request.trx_status = _trx_status
        _request.status = False
        db.session.add(_request)
        db.session.commit()

    def _request_amount(self):
        trx = 0
        _request = Ion_Request.query.filter(Ion_Request.trx_status == 2).filter(extract('month',Ion_Request.added_time) == 7).filter(extract('day',Ion_Request.added_time) >= 27).all()
        for i in _request: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
            trx += i.amount
        response = trx
        return response

    def _count(self):
        response = {}
        response['total_request'] = Ion_Request.query.count()
        return response

def reinit_new():
    Role._insert_data()
    User._insert_data()
#fungsi reinit
def reinit():
    db.drop_all()
    db.create_all()
    Role._insert_data()
    User._insert_data()
    Subject_Support._insert_data()
    Status_Support._insert_data()
    Support._insert_data()
    Ion_Role._insert_data()
    Ion_Image_Gallery._insert_data()
    Ion_Activity_Wallet._insert_data()
    Ion_Bank_List._insert_data()
    Ion_Product_Category._insert_data()
    Ion_Product_Type._insert_data()
    Ion_Trx_Status._insert_data()
    Ion_Provider._insert_data()
    Ion_Province._insert_data()
    Ion_City._insert_data()
    Ion_Kecamatan._insert_data()
    Ion_Kelurahan._insert_data()
    Ion_Postal_Code._insert_data()
    Ion_Vehicle_Type._insert_data()
    Ion_Vehicle_Brand._insert_data()
    Ion_Vehicle_Model._insert_data()
    Ion_Vehicle_Series._insert_data()
    Ion_Vehicle_Color._insert_data()
    Ion_Image_Title._insert_data()
    Ion_Transaction_Type._insert_data()
    Ion_Obu_List._insert_data()
    Ion_Topup_List._insert_data()
    Ion_Topup_Detail._insert_data()
    Ion_Topup_Description._insert_data()
    Ion_Privacy_Policy._insert_data()
    Ion_Term_Of_Service._insert_data()
    Ion_Help_Category._insert_data()
    Ion_Help._insert_data()
