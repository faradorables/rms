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
    return User.query.get(int(user_id))

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
        User()._insert('Farah Shahnaz Imami', '08975181009', 'farah@ion-network.id', '!2345ion5432!', '123456',  _role_id=1)
        print('Done!')

class Hop_User(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'user'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    phone_number = db.Column(db.String(50),index=True)
    password_hash = db.Column(db.String(128))
    pin_hash = db.Column(db.String(128))
    email = db.Column(db.String(100),index=True)
    outlet_id = db.Column(db.Integer,db.ForeignKey('outlet.id'))
    role_id = db.Column(db.Integer,db.ForeignKey('role.id'))
    address = db.Column(db.Text)
    gender_id = db.Column(db.String(15))
    birthdate = db.Column(db.DateTime)
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insertowner(self, _name, _phonenumber, _password, _pin, _email, _role, _address, _gender, _birthdate):
        insert = Hop_User()
        insert.name = _name
        insert.phone_number = _phonenumber
        insert.password_hash = generate_password_hash(_password)
        insert.pin_hash = generate_password_hash(_pin)
        insert.email = _email
        insert.outlet_id = None
        insert.role_id = _role
        insert.address = _address
        insert.gender_id = _gender
        insert.birthdate = datetime.strptime(_birthdate, '%Y-%m-%d')
        insert.add_time = datetime.now()
        db.session.add(insert)
        db.session.commit()
        return insert

    def _updateowner(self, _id, _name, _phonenumber, _email, _role, _address, _gender, _birthdate):
        update = Hop_User()
        update = Hop_User.query.filter_by(id=_id).first()
        update.name = _name
        update.phone_number = _phonenumber
        update.email = _email
        update.role_id = _role
        update.address = _address
        update.gender_id = _gender
        update.birthdate = _birthdate
        db.session.add(update)
        db.session.commit()

    def _insertuser(self, _name, _phonenumber, _password, _pin, _email, _outlet, _role, _address, _gender, _birthdate):
        insert = Hop_User()
        insert.name = _name
        insert.phone_number = _phonenumber
        insert.password_hash = generate_password_hash(_password)
        insert.pin_hash = generate_password_hash(_pin)
        insert.email = _email
        insert.outlet_id = _outlet
        insert.role_id = _role
        insert.address = _address
        insert.gender_id = _gender
        insert.birthdate = datetime.strptime(_birthdate, '%Y-%m-%d')
        insert.add_time = datetime.now()
        db.session.add(insert)
        db.session.commit()
        return insert

    def _updateuser(self, _id, _name, _phonenumber, _password, _pin, _email, _outlet, _role, _address, _gender, _birthdate):
        update = Hop_User()
        update = Hop_User.query.filter_by(id=_id).first()
        update.name = _name
        update.phone_number = _phonenumber
        update.password_hash = generate_password_hash(_password)
        update.pin_hash = generate_password_hash(_pin)
        update.email = _email
        update.outlet_id = _outlet
        update.role_id = _role
        update.address = _address
        update.gender_id = _gender
        update.birthdate = _birthdate
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        remove = Hop_User()
        remove = Hop_User.query.filter_by(id = _id).first()
        remove.status = False
        db.session.add(remove)
        db.session.commit()

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

    def check_pin(self,pin):
        return check_password_hash(self.pin_hash,pin)

    def generate_token(self):
        key = str.encode(self.phone_number)
        msg = str.encode(str(self.id) + ':' + str(self.phone_number) + ':' + str(self.password_hash) + ':' + str(self.pin_hash))
        return hmac_sha256(key, msg)

    def verify_token(self, token):
        response = False
        key = str.encode(self.phone_number)
        msg = str.encode(str(self.id) + ':'+ str(self.phone_number) + ':' + str(self.password_hash) + ':' + str(self.pin_hash))
        if token == hmac_sha256(key, msg):
            response = True
        return response

    def _data(self,_id):
        response = {}
        _user = Hop_User.query.filter_by(id = _id, status = True).first()
        if _user is not None:
            response['id'] =  _user.id
            response['name'] =  _user.name
            response['phone_number'] =  _user.phone_number
            response['email'] =  _user.email
            response['outlet_id'] =  _user.outlet_id
            response['role_id'] =  _user.role_id
            response['address'] =  _user.address
        else:
            print(response)
        return response

    def _list(self, limit=25, page=0):
        response = []
        _user = Hop_User.query.filter_by(status = True).all()
        for i in _user:
            response.append({
                'id' : i.id ,
                'name' : i.name ,
                'phone_number' : i.phone_number,
                'email' : i.email,
                # 'birthdate' : i.birthdate.strftime("%m-%d-%Y"),
                'address' : i.address,
                'role' : Hop_Role()._data(i.role_id),
                # 'outlet' : Hop_Outlet()._data(i.outlet_id)
            })
        return response

    def _count (self):
        response = {}
        response['total_user'] = Hop_User.query.filter_by(status=True).count()
        response['total_outlet'] = Hop_Outlet.query.filter_by(status=True).count()
        return response

class Hop_Outlet(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'outlet'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.Text)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    email = db.Column(db.String(100),index=True)
    phone_number = db.Column(db.String(50),index=True)
    address = db.Column(db.Text)
    province_id = db.Column(db.Integer,db.ForeignKey('province.id'))
    city_id = db.Column(db.Integer,db.ForeignKey('city.id'))
    district_id = db.Column(db.Integer,db.ForeignKey('district.id'))
    sub_district_id = db.Column(db.String(20),db.ForeignKey('sub_district.id'))
    postal_code_id = db.Column(db.Integer, db.ForeignKey('postal_code.id'))
    status_address_id = db.Column(db.Integer, db.ForeignKey('list_status_address.id'))
    rt = db.Column(db.String(4))
    rw = db.Column(db.String(4))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _name, _userid, _phonenumber, _address, _province, _city, _kecamatan, _kelurahan,  _postalcode, _rt, _rw, _statusaddress):
        insert = Hop_Outlet()
        insert.name = _name
        insert.user_id = _userid
        insert.phone_number = _phonenumber
        insert.address = _address
        insert.province_id = _province
        insert.city_id = _city
        insert.kecamatan_id = _kecamatan
        insert.kelurahan_id = _kelurahan
        insert.postal_code_id = _postalcode
        insert.status_address_id = _statusaddress
        insert.rt = _rt
        insert.rw = _rw
        insert.add_time = datetime.now()
        db.session.add(insert)
        db.session.commit()


    def _update(self, _id, _name, _userid, _phonenumber, _address, _province, _city, _kecamatan, _kelurahan,  _postalcode, _rt, _rw, _statusaddress):
        update = Hop_Outlet()
        update = Hop_Outlet.query.filter_by(id=_id).first()
        update.name = _name
        update.user_id = _userid
        update.phone_number = _phonenumber
        update.address = _address
        update.province_id = _province
        update.city_id = _city
        update.kecamatan_id = _kecamatan
        update.kelurahan_id = _kelurahan
        update.postal_code_id = _postalcode
        update.status_address_id = _statusaddress
        update.rt = _rt
        update.rw = _rw
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        remove = Hop_Outlet()
        remove = Hop_Outlet.query.filter_by(id = _id).first()
        remove.status = False
        db.session.add(remove)
        db.session.commit()

    def _data(self, outlet_id):
        response = {}
        _outlet = Hop_Outlet.query.filter_by(id = outlet_id, status = True).first()
        _city = Hop_City.query.filter_by(id = _outlet.city_id).first()
        _prov = Hop_Province.query.filter_by(id = _outlet.province_id).first()
        if _outlet is not None:
            response['id'] =  _outlet.id
            response['name'] =  _outlet.name
            response['address'] =  _outlet.address
            response['city'] =  _city.name
            response['province'] =  _prov.name
        return response

    def _count (self, user_id):
        response = {}
        response['total_user'] = Hop_User.query.filter_by(status=True).count()
        response['total_outlet'] = Hop_Outlet.query.filter_by(status=True).count()
        response['outlet_by_user'] = Hop_Outlet.query.filter_by(status=True, user_id=user_id).count()
        return response

    def _list(user_id, limit=25, page=0):
        response = []
        _outlet = Hop_Outlet.query.filter_by(status = True).all()
        for i in _outlet:
            user = Hop_User.query.filter_by(id=i.user_id).first()
            city = Hop_City.query.filter_by(id=i.city_id).first()
            province = Hop_Province.query.filter_by(id=i.province_id).first()
            response.append({
                'id' : i.id ,
                'name' : i.name,
                'user' : user.name,
                'email': i.email,
                'address' : i.address,
                'city': city.name,
                'province': province.name,
                'phone_number' : i.phone_number
            })
        return response

    def _list_by_user(self, user_id):
        response = []
        _outlet = Hop_Outlet.query.filter_by(status = True, user_id=user_id).all()
        for i in _outlet:
            user = Hop_User.query.filter_by(id=i.user_id).first()
            city = Hop_City.query.filter_by(id=i.city_id).first()
            province = Hop_Province.query.filter_by(id=i.province_id).first()
            response.append({
                'id' : i.id ,
                'name' : i.name,
                'user' : user.name,
                'email': i.email,
                'address' : i.address,
                'city': city.name,
                'province': province.name,
                'phone_number' : i.phone_number
            })
        return response

class Hop_Role(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'role'
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _name):
        insert = Hop_Role()
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)
        db.session.commit()

    def _update(self, _id, _name):
        update = Hop_Role()
        update = Hop_Role.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = Hop_Role()
        update = Hop_Role.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _data(self, _id):
        response = {}
        _role = Hop_Role.query.filter_by(id = _id).filter_by(status = True).first()
        if _role is not None:
            response['id'] = _role.id
            response['name'] = _role.name
        return response

    def _list(self):
        response = {}
        response['data'] = []
        _role = Hop_Role.query.filter_by(status = True).all()
        for i in _role:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name
            })
        return response

class Hop_Province(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'province'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name):
        insert = Hop_Province()
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name):
        update = Hop_Province()
        update = Hop_Province.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = Hop_Province()
        update = Hop_Province.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _province = Hop_Province.query.filter_by(status = True).order_by(Hop_Province.name.asc()).all()
        for i in _province:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name
            })
        return response

    def _data(self, _id):
        response = {}
        _province = Hop_Province.query.filter_by(id = _id, status = True).first()
        if _province is not None:
            response['id'] = _province.id
            response['name'] = _province.name
        return response

class Hop_City(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'city'

    id = db.Column(db.Integer,primary_key=True)
    province_id = db.Column(db.Integer,db.ForeignKey('province.id'))
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _province):
        insert = Hop_City()
        insert.province_id = _province
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _province):
        update = Hop_City()
        update = Hop_City.query.filter_by(id = _id).first()
        update.province_id = _province
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = Hop_City()
        update = Hop_City.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self, _id):
        response = {}
        response['data'] = []
        _city = Hop_City.query.filter_by(province_id = _id).filter_by(status = True).order_by(Hop_City.name.asc()).all()
        for i in _city:
            response['data'].append({
                'id' : i.id,
                'province_id' : i.province_id,
                'name' : i.name
            })
        return response

    def _listall(self):
        response = {}
        response['data'] = []
        _city = Hop_City.query.filter_by(status = True).all()
        for i in _city:
            response['data'].append({
                'id' : i.id,
                'province_id' : i.province_id,
                'name' : i.name
            })
        return response

    def _data(self,_id):
        response = {}
        _city = Hop_City.query.filter_by(id = _id).filter_by(status = True).first()
        if _city is not None:
            response['id'] = _city.id
            response['province_id'] = _city.province_id
            response['name'] = _city.name
        return response

class Hop_District(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'district'

    id = db.Column(db.Integer,primary_key=True)
    city_id = db.Column(db.Integer,db.ForeignKey('city.id'))
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _city):
        insert = Hop_District()
        insert.city_id = _city
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _idcity):
        update = Hop_District()
        update = Hop_District.query.filter_by(id = _id).first()
        update.city_id = _idcity
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = Hop_District()
        update = Hop_District.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self,_id):
        response = {}
        response['data'] = []
        _kecamatan = Hop_District.query.filter_by(city_id = _id).filter_by(status = True).order_by(kecamatan.name.asc()).all()
        for i in _kecamatan:
            response['data'].append({
                'id' : i.id,
                'city_id' : i.city_id,
                'name' : i.name
            })
        return response

    def _listall(self):
        response = {}
        response['data'] = []
        _kecamatan = Hop_District.query.filter_by(status = True).all()
        for i in _kecamatan:
            response['data'].append({
                'id' : i.id,
                'city_id' : i.city_id,
                'name' : i.name
            })
        return response
    def _data(self, _id):
        response = {}
        _kecamatan = Hop_District.query.filter_by(id = _id).filter_by(status = True).first()
        if _kecamatan is not None:
            response['id'] = _kecamatan.id
            response['city_id'] = _kecamatan.city_id
            response['name'] = _kecamatan.name
        return response

class Hop_Sub_District(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'sub_district'

    id = db.Column(db.String(20),primary_key=True)
    district_id = db.Column(db.Integer,db.ForeignKey('district.id'))
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _kecamatan):
        insert = Hop_Sub_District()
        insert.kecamatan_id = _kecamatan
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _kecamatan):
        update = Hop_Sub_District()
        update = Hop_Sub_District.query.filter_by(id = _id).first()
        update.name = _name
        update.kecamatan_id = _kecamatan
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = Hop_Sub_District()
        update = Hop_Sub_District.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self,_id):
        response = {}
        response['data'] = []
        _kelurahan = Hop_Sub_District.query.filter_by(kecamatan_id = _id).filter_by(status = True).order_by(Hop_Sub_District.name.asc()).all()
        for i in _kelurahan:
            response['data'].append({
                'id' : i.id,
                'kecamatan_id' : i.kecamatan_id,
                'name' : i.name
            })
        return response

    def _listall(self):
        response = {}
        response['data'] = []
        _kelurahan = Hop_Sub_District.query.filter_by(status = True).all()
        for i in _kelurahan:
            response['data'].append({
                'id' : i.id,
                'kecamatan_id' : i.kecamatan_id,
                'name' : i.name
            })
        return response

    def _data(self,_id):
        response = {}
        _kelurahan = Hop_Sub_District.query.filter_by(id = _id).filter_by(status = True).first()
        if _kelurahan is not None:
            response['id'] = _kelurahan.id
            response['kecamatan_id'] = _kelurahan.kecamatan_id
            response['name'] = _kelurahan.name
        return response

class Hop_Postal_Code(db.Model,UserMixin):
    __bind_key__ = 'hop'
    __tablename__ = 'postal_code'

    id = db.Column(db.Integer,primary_key=True)
    sub_district_id = db.Column(db.String(20),db.ForeignKey('sub_district.id'))
    name = db.Column(db.String(6))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _kelurahan):
        insert = Hop_Postal_Code()
        insert.kelurahan_id = _kelurahan
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _kelurahan):
        update = Hop_Postal_Code()
        update = Hop_Postal_Code.query.filter_by(id = _id).filter_by(status = True).first()
        upadte.kelurahan_id = _kelurahan
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = Hop_Postal_Code()
        update = Hop_Postal_Code.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self,_kelurahan):
        response = {}
        response['data'] = []
        _postalcode = Hop_Postal_Code.query.filter_by(status = True, kelurahan_id = _kelurahan).all()
        for i in _postalcode:
            response['data'].append({
                'id' : i.id,
                'kelurahan_id' : i.kelurahan_id,
                'name' : i.name
            })
        return response

    def _listall(self):
        response = {}
        response['data'] = []
        _postalcode = Hop_Postal_Code.query.filter_by(status = True).all()
        for i in _postalcode:
            response['data'].append({
                'id' : i.id,
                'kelurahan_id' : i.kelurahan_id,
                'name' : i.name
            })
        return response

    def _data(self,_id):
        response = {}
        _postalcode = Hop_Postal_Code.query.filter_by(id = _id).filter_by(status = True).first()
        if _postalcode is not None:
            response['id'] = _postalcode.id
            response['kelurahan_id'] = _postalcode.kelurahan_id
            response['name'] = _postalcode.name
        return response

class Hop_List_Status_Address(db.Model,UserMixin):
    __tablename__ = 'list_status_address'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name):
        insert = Hop_List_Status_Address()
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name):
        update = Hop_List_Status_Address()
        update = Hop_List_Status_Address.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _statusaddress = Hop_List_Status_Address.query.filter_by(status = True).all()
        for i in _statusaddress:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name
            })
        return response

#fungsi reinit
def reinit():
    # db.drop_all()
    # db.create_all()
    Role._insert_data()
    User._insert_data()
