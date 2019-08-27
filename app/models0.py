from datetime import datetime
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import create_engine
from markdown import markdown
import bleach
from flask import current_app, request, url_for, Flask
from flask_login import UserMixin, AnonymousUserMixin
from app.exceptions import ValidationError
from . import db, login_manager
from .utils import hmac_sha256, engine_mysql
from . import mongo
import pymongo, requests
from bson import ObjectId
import os,time
from os.path import join, dirname, realpath
from werkzeug.utils import secure_filename

# engine = create_engine('mysql://root@localhost:3306/ion')
engine = create_engine('mysql://ionapi:!2345iondbapi5432!@209.97.175.39:3306/ion')

apps = Flask(__name__)

class Role(db.Model):
    __tablename__ = 'ion_roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ['User', 'BUJT', 'Merchant']
        for v in values:
            role = Role()
            role.name = v
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name

class Bank_List(db.Model):
    __tablename__ = 'ion_bank_list'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    uid = db.Column(db.String(64), unique=True, index=True)
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    bank_account = db.relationship('Bank_Account', backref='Bank_list', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "BRI", "uid": "002", "image_id":"5"},
            {"name" : "BNI", "uid": "009", "image_id":"6"},
            {"name" : "BCA", "uid": "014", "image_id":"7"},
            {"name" : "MANDIRI", "uid": "008", "image_id":"8"},
            {"name" : "BRI SYARIAH", "uid": "422", "image_id":"9"},
            {"name" : "BNI SYARIAH", "uid": "427", "image_id":"10"},
            {"name" : "BCA SYARIAH", "uid": "536", "image_id":"11"},
            {"name" : "MANDIRI SYARIAH", "uid": "451", "image_id":"12"}
        ]
        for v in values:
            _bank = Bank_List()
            _bank.name = v['name']
            _bank.uid = v['uid']
            _bank.image_id = v['image_id']
            db.session.add(_bank)
            db.session.commit()

    def _list(self):
        response = {}
        response = []
        _list = Bank_List.query.filter_by(status=True).all()
        for i in _list:
            response.append({
                'id': i.id,
                'name': i.name,
                'uid': i.uid
            })
        return response


class Bank_Account(db.Model):
    __tablename__ = 'ion_bank_account'
    id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(124))
    account_number = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    bank_id = db.Column(db.Integer, db.ForeignKey('ion_bank_list.id'))
    default = db.Column(db.Boolean)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    def _insert(self, _acc_name, _acc_number, _user_id, _bank_id):
        _check_row = Bank_Account.query.filter_by(user_id=_user_id, status=True).all() #lihat semua row dengan uid untuk melakukan cek use count
        if len(_check_row) > 0:
            _bank_acc = Bank_Account()
            _bank_acc.account_name = _acc_name
            _bank_acc.account_number = _acc_number
            _bank_acc.user_id = _user_id
            _bank_acc.bank_id = _bank_id
            _bank_acc.default = False
            db.session.add(_bank_acc)
            db.session.commit()

        else:
            _bank_acc = Bank_Account()
            _bank_acc.account_name = _acc_name
            _bank_acc.account_number = _acc_number
            _bank_acc.user_id = _user_id
            _bank_acc.bank_id = _bank_id
            _bank_acc.default = True
            db.session.add(_bank_acc)
            db.session.commit()

    def _list(self, _user_id):
        response = {}
        response = []
        _list = Bank_Account.query.filter_by(user_id=_user_id, status=True).all()
        for i in _list:
            _bank = Bank_List.query.filter_by(id=i.bank_id, status=True).first()
            _bank_image = Image_Gallery.query.filter_by(id=_bank.image_id, status=True).first()
            response.append({
                'id': i.id,
                'account_number': i.account_number,
                'account_name': i.account_name,
                'default': i.default,
                'uid': _bank.uid,
                'image_name': _bank_image.image_name,
                'bank': _bank.name
            })
        return response

    def _data(self, _id):
        response = {}
        _account = Bank_Account.query.filter_by(id=_id, status=True).first()
        _bank = Bank_List.query.filter_by(id=_account.bank_id, status=True).first()
        response['id'] = _account.id
        response['account_name'] = _account.account_name
        response['account_number'] = _account.account_number
        response['user_id'] = _account.user_id
        response['bank'] = _bank.name
        return response

    def _update(self, _id,_acc_name, _acc_number, _user_id, _bank_id):
        _bank_acc = Bank_Account.query.filter_by(id=_id).first()
        _bank_acc.account_name = _acc_name
        _bank_acc.account_number = _acc_number
        _bank_acc.user_id = _user_id
        _bank_acc.bank_id = _bank_id
        db.session.add(_bank_acc)
        db.session.commit()

    def _udpate_default(self, _id, _user_id):
        Bank_Account()._default_false(_user_id)
        _update_bank = Bank_Account.query.filter_by(id=_id).first()
        _update_bank.default = True
        db.session.add(_update_bank)
        db.session.commit()

    def _default_false(self, _user_id):
        _bank_acc = Bank_Account.query.filter_by(user_id=_user_id, default=True).first()
        _bank_acc.default = False
        db.session.add(_bank_acc)
        db.session.commit()

    def _delete(self, _id):
        _account = Bank_Account.query.filter_by(id=_id).first()
        _account.default = False
        _account.status = False
        db.session.add(_account)
        db.session.commit()

    def _change_default(self, _user_id, _id):
        _check_row = Bank_Account.query.filter_by(user_id=_user_id, status=True).all()
        if len(_check_row) > 0:
            Bank_Account()._delete(_id)
            _account = Bank_Account.query.filter_by(user_id=_user_id, status=True).first()
            _account.default = True
            db.session.add(_account)
            db.session.commit()
        else:
            Bank_Account()._delete(_id)


class Wallet(db.Model):
    __tablename__ = 'ion_wallet'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('ion_activity_wallet.id'))
    amount = db.Column(db.Integer, default=0)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    #melakukan check saldo pada table wallet berdasarkan id
    def _check(self, _id):
        response = {}
        debit = 0 #set debit ke 0
        credit = 0 #set credit ke 0
        user = User.query.filter_by(id=_id).first()
        if user is not None:
            _wallet = Wallet.query.filter_by(user_id=user.id, status=True).all()
            for i in _wallet: #pengulangan dalam wallet berdasarkan id yang dikirim. seperti query diatas
                if i.type_id == 1: #status 1 adalah debit
                    debit += i.amount #debit = debit(0) nilai awal yang telah di set + amount yang ada, kemudian debit terisi berdasarkan nilai jumlahnya
                elif i.type_id == 2: #status 2 adalah credit
                    credit += i.amount #credit = credit(0) nilai awal yang telah di set + amount yang ada, kemudian credit terisi berdasarkan nilai jumlahnya
        response = debit - credit
        return response

    def _insert(self, _id, _type, _amount):
        _wallet = Wallet()
        _wallet.user_id = _id
        _wallet.type_id = int(_type)
        _wallet.amount = _amount
        _wallet.added_time =  datetime.now()
        db.session.add(_wallet)
        db.session.commit()
        response = Wallet()._data(_wallet.id, _id)
        return response

    def _data(self, user_id, _id):
        response = {}
        _wallet = Wallet.query.filter_by(id=_id, user_id=user_id, status=True).first()
        if _wallet is not None:
            response['id'] = _wallet.id
            response['user_id'] = _wallet.user_id
            response['amount'] = _wallet.amount
            response['timestamp'] = _wallet.added_time
        return response

class Point(db.Model):
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
        user = User.query.filter_by(id=_id).first()
        if user is not None:
            _point = Point.query.filter_by(user_id=user.id, status=True).all()
            for i in _point:
                if i.type_id == 1:
                    debit += i.amount
                elif i.type_id == 2:
                    credit += i.amount
        response = debit - credit
        return response

    def _data(self, user_id, _id):
        response = {}
        _point = Point.query.filter_by(id=_id, user_id=user_id, status=True).first()
        if _point is not None:
            response['id'] = _point.id
            response['user_id'] = _point.user_id
            response['amount'] = _point.amount
            response['timestamp'] = _point.added_time
        return response

class Activity_Wallet(db.Model):
    __tablename__ = 'ion_activity_wallet'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    wallet = db.relationship('Wallet', backref='activity_wallet', lazy='dynamic')
    product_type = db.relationship('Product_Type', backref='activity_wallet', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ['Debit', 'Credit','Pending']
        for v in values:
            _type = Activity_Wallet()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

    def _data(seld, _id):
        response = {}
        _trx = Activity_Wallet.query.filter_by(id=_id, status=True).first()
        response['id'] = _trx.id
        response['name'] = _trx.name
        return response

class Trx_Status(db.Model):
    __tablename__ = 'ion_trx_status'
    id = db.Column(db.Integer, primary_key=True)
    status_code = db.Column(db.String(10))
    name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    image_service = db.relationship('Image_Service', backref='trx_status', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"status_code" : "50", "name": "Failed"},
            {"status_code" : "00", "name": "Success"},
            {"status_code" : "60", "name": "Pending"},
            {"status_code" : "70", "name": "Reject"}
        ]
        for v in values:
            _status = Trx_Status()
            _status.status_code = v['status_code']
            _status.name = v['name']
            db.session.add(_status)
            db.session.commit()

class Image_Gallery(db.Model):
    __tablename__ = 'ion_image_gallery'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    image_name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    product_category = db.relationship('Product_Category', backref='Image_Gallery', lazy='dynamic')
    help_category = db.relationship('Help_Category', backref='Image_Gallery', lazy='dynamic')
    # vehicle_brand = db.relationship('Vehicle_Brand', backref='Image_Gallery', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"title" : "IONCASH", "image_name": "ion-cash.png"},
            {"title" : "Pulsa", "image_name": "pulsa.png"},
            {"title" : "Hotel", "image_name": "hotel.png"},
            {"title" : "Obu Transaction", "image_name": "obu.png"},
            {"title" : "BRi", "image_name": "bri.png"},
            {"title" : "BNI", "image_name": "bni.png"},
            {"title" : "BCA", "image_name": "bca.png"},
            {"title" : "MANDIRI", "image_name": "mandiri.png"},
            {"title" : "BRi SYARIAH", "image_name": "bri-syariah.png"},
            {"title" : "BNI SYARIAH", "image_name": "bni-syariah.png"},
            {"title" : "BCA SYARIAH", "image_name": "bca-syariah.png"},
            {"title" : "MANDIRI SYARIAH", "image_name": "mandiri-syariah.png"}
        ]
        for v in values:
            _img = Image_Gallery()
            _img.title = v['title']
            _img.image_name = v['image_name']
            db.session.add(_img)
            db.session.commit()

class Product_Category(db.Model):
    __tablename__ = 'ion_product_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    provider_id = db.Column(db.Integer, db.ForeignKey('ion_provider.id'))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    point = db.relationship('Point', backref='Product_Category', lazy='dynamic')
    product_type = db.relationship('Product_Type', backref='Product_Category', lazy='dynamic')
    inbox = db.relationship('Inbox', backref='Product_Category', lazy='dynamic')
    ion_request = db.relationship('Request', backref='Product_Category', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = [
            {"name" : "IONCASH", "image_id": 1},
            {"name" : "Pulsa", "image_id": 2},
            {"name" : "Hotel", "image_id": 3},
            {"name" : "Obu Transaction", "image_id": 4}
        ]
        for v in values:
            _cat = Product_Category()
            _cat.name = v['name']
            _cat.image_id = v['image_id']
            db.session.add(_cat)
            db.session.commit()

class Product_Type(db.Model):
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
            _types = Product_Type()
            _types.name = v
            db.session.add(_types)
            db.session.commit()

class Provider(db.Model):
    __tablename__ = 'ion_provider'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    image = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    product_category = db.relationship('Product_Category', backref='Provider', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ['Ion']
        for v in values:
            provider = Provider()
            provider.name = v
            db.session.add(provider)
            db.session.commit()

class Identity(db.Model):
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
        _identity = Identity()
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
        _identity = Identity.query.filter_by(user_id=_id, status=True).first()
        response['id'] = _identity.id
        response['user_id'] = _identity.user_id
        response['profile_photo'] = _identity.profile_photo
        response['nik'] = _identity.nik
        response['province_id'] = _identity.province_id
        response['city_id'] = _identity.city_id
        response['kecamatan_id'] = _identity.kecamatan_id
        response['kelurahan_id'] = _identity.kelurahan_id
        response['address'] = _ident.address
        response['postal_code_id'] = _identity.postal_code_id
        response['photo_ktp'] = _identity.photo_ktp
        response['selfie_idcard'] = _identity.selfie_idcard
        return response

    def _update(self, _id, _user_id, _profil_photo, _nik, _province_id, _city_id, _kecamatan_id, _kelurahan_id, _address, _postal_code, _photo_ktp, _selfie_idcard):
        _identity = Identity()
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
        response = Identity()._data(_identity.user_id)
        return response

    def _delete(self, _id):
        _identity = Identity.query.filter_by(id=_id, status=True).first()
        _identity.status = False #set status false
        db.session.add(_identity) #update status false untuk data sebelumnya
        db.session.commit()

class Correspondent_Address(db.Model):
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

class Province(db.Model):
    __tablename__ = 'ion_province'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class City(db.Model):
    __tablename__ = 'ion_city'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    province_id = db.Column(db.Integer, db.ForeignKey('ion_province.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Kecamatan(db.Model):
    __tablename__ = 'ion_kecamatan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    city_id = db.Column(db.Integer, db.ForeignKey('ion_city.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Kelurahan(db.Model):
    __tablename__ = 'ion_kelurahan'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    kecamatan_id = db.Column(db.Integer, db.ForeignKey('ion_kecamatan.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Postal_Code(db.Model):
    __tablename__ = 'ion_postal_code'
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(128))
    kelurahan_id = db.Column(db.Integer, db.ForeignKey('ion_kelurahan.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Obu_Detail(db.Model):
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

class Obu_List(db.Model):
    __tablename__ = 'ion_obu_list'
    id = db.Column(db.Integer, primary_key=True)
    obu_uid = db.Column(db.String(128))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'), default=None)
    pin_hash = db.Column(db.String(128))
    use_count = db.Column(db.Integer, default=1)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    #relationship
    obu_detail = db.relationship('Obu_Detail', backref='obu_list', lazy='dynamic')

class Plate_Expired(db.Model):
    __tablename__ = 'ion_plate_expired'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'), default=None)
    plate_id = db.Column(db.String(64))
    obu_id = db.Column(db.Integer, db.ForeignKey('ion_obu_list.id'))
    expired_month =  db.Column(db.Integer)
    expired_year = db.Column(db.Integer)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Vehicle_Type(db.Model):
    __tablename__ = 'ion_vehicle_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    #relationship
    vehicle_brand = db.relationship('Vehicle_Brand', backref='Vehicle_Type', lazy='dynamic')
    obu_detail = db.relationship('Obu_Detail', backref='Vehicle_Type', lazy='dynamic')

class Vehicle_Model(db.Model):
    __tablename__ = 'ion_vehicle_model'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    vehicle_series = db.relationship('Vehicle_Series', backref='Vehicle_Model', lazy='dynamic')
    obu_detail = db.relationship('Obu_Detail', backref='Vehicle_Model', lazy='dynamic')

class Vehicle_Brand(db.Model):
    __tablename__ = 'ion_vehicle_brand'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    type_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_type.id'))
    # image_id = db.Column(db.Integer, db.ForeignKey('image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    vehicle_series = db.relationship('Vehicle_Series', backref='Vehicle_Brand', lazy='dynamic')
    obu_detail = db.relationship('Obu_Detail', backref='Vehicle_Brand', lazy='dynamic')

class Vehicle_Series(db.Model):
    __tablename__ = 'ion_vehicle_series'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    brand_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_brand.id'))
    type_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_type.id'))
    model_id = db.Column(db.Integer, db.ForeignKey('ion_vehicle_model.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    obu_detail = db.relationship('Obu_Detail', backref='Vehicle_Series', lazy='dynamic')

class Vehicle_Color(db.Model):
    __tablename__ = 'ion_vehicle_color'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    obu_detail = db.relationship('Obu_Detail', backref='Vehicle_Color', lazy='dynamic')

class Inbox(db.Model):
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

class Inbox_Upgrade(db.Model):
    __tablename__ = 'ion_inbox_upgrade'
    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.String(128))
    content = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    icon_image = db.Column(db.String(255))
    product_category_id = db.Column(db.Integer, db.ForeignKey('ion_product_category.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Request(db.Model):
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

class Image_Service(db.Model):
    __tablename__ = 'ion_image_service'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    image_title_id = db.Column(db.Integer, db.ForeignKey('ion_image_title.id'))
    verification_id = db.Column(db.Integer, db.ForeignKey('ion_trx_status.id'), default=2)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    updated_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Image_Title(db.Model):
    __tablename__ = 'ion_image_title'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    image_service = db.relationship('Image_Service', backref='Image_Title', lazy='dynamic')

class Transaction_Type(db.Model):
    __tablename__ = 'ion_transaction_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    topup_detail = db.relationship('Topup_List', backref='Transaction_Type', lazy='dynamic')

class Status_Upgrade(db.Model):
    __tablename__ = 'ion_status_upgrade'
    id = db.Column(db.Integer, primary_key=True)
    status_upgrade = db.Column(db.Integer)
    description = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    ion_upgrade = db.relationship('Upgrade', backref='Status_Upgrade', lazy='dynamic')

class Upgrade(db.Model):
    __tablename__ = 'ion_upgrade'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_trx_status.id'), default=2)
    id_card = db.Column(db.String(128))
    selfie_photo = db.Column(db.String(128))
    status_upgrade_id = db.Column(db.Integer, db.ForeignKey('ion_status_upgrade.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    ion_upgrade = db.relationship('User', backref='Upgrade', lazy='dynamic')

class Notification_Type(db.Model):
    __tablename__ = 'ion_notification_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(74))
    page = db.Column(db.String(64))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    notification = db.relationship('Notification', backref='Notification_Type', lazy='dynamic')

class Notification(db.Model):
    __tablename__ = 'ion_notification'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    notification_type = db.Column(db.Integer, db.ForeignKey('ion_notification_type.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Topup_List(db.Model):
    __tablename__ = 'ion_topup_list'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    transaction_type = db.Column(db.Integer, db.ForeignKey('ion_transaction_type.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    topup_detail = db.relationship('Topup_Detail', backref='Topup_List', lazy='dynamic')

class Topup_Detail(db.Model):
    __tablename__ = 'ion_topup_detail'
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey('ion_topup_list.id'))
    title = db.Column(db.String(64))
    code_bank = db.Column(db.String(32))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    topup_description = db.relationship('Topup_Description', backref='Topup_Detail', lazy='dynamic')

class Topup_Description(db.Model):
    __tablename__ = 'ion_topup_description'
    id = db.Column(db.Integer, primary_key=True)
    detail_id = db.Column(db.Integer, db.ForeignKey('ion_topup_detail.id'))
    description = db.Column(db.String(255))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Privacy_Policy(db.Model):
    __tablename__ = 'ion_privacy_policy'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Term_Of_Service(db.Model):
    __tablename__ = 'ion_term_of_service'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    description = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Help_Category(db.Model):
    __tablename__ = 'ion_help_category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(125))
    image_id = db.Column(db.Integer, db.ForeignKey('ion_image_gallery.id'))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    help = db.relationship('Help', backref='Help_Category', lazy='dynamic')

class Help(db.Model):
    __tablename__ = 'ion_help'
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('ion_help_category.id'))
    title = db.Column(db.String(64))
    description = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class Activity_Type(db.Model):
    __tablename__ = 'ion_activity_type'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

    log_activity = db.relationship('Log_Activity', backref='Activity_Type', lazy='dynamic')

    @staticmethod
    def _insert_data():
        values = ["Register", "Login", "Transfer Money", "Topup", "History"]
        for v in values:
            _type = Activity_Type()
            _type.name = v
            db.session.add(_type)
            db.session.commit()

class Log_Activity(db.Model):
    __tablename__ = 'ion_log_activity'
    id = db.Column(db.Integer, primary_key=True)
    user_id =  db.Column(db.Integer, db.ForeignKey('ion_users.id'))
    activity_type_id =  db.Column(db.Integer, db.ForeignKey('ion_activity_type.id'))
    ip_address = db.Column(db.String(255))
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)

class User(UserMixin, db.Model):
    __tablename__ = 'ion_users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128))
    phone_number = db.Column(db.String(20))
    email = db.Column(db.String(64))
    pin_hash = db.Column(db.String(128))
    bri_va = db.Column(db.String(64))
    bca_va = db.Column(db.String(64))
    mandiri_va = db.Column(db.String(64))
    bni_va = db.Column(db.String(64))
    role_id = db.Column(db.Integer, db.ForeignKey('ion_roles.id'), default=1)
    firebase_id = db.Column(db.String(255))
    tos_agreement = db.Column(db.Boolean, default=False)
    added_time = db.Column(db.DateTime(), default=datetime.now())
    status = db.Column(db.Boolean, default=True)
    confirmed = db.Column(db.Boolean, default=False)
    id_upgrade = db.Column(db.Integer, db.ForeignKey('ion_upgrade.id'))
    verified = db.Column(db.Boolean, default=False)

    bank_account = db.relationship('Bank_Account', backref='User', lazy='dynamic')
    identity = db.relationship('Identity', backref='User', lazy='dynamic')
    wallet = db.relationship('Wallet', backref='User', lazy='dynamic')
    correspondent_address = db.relationship('Correspondent_Address', backref='User', lazy='dynamic')
    obu_list = db.relationship('Obu_List', backref='User', lazy='dynamic')
    obu_detail = db.relationship('Obu_Detail', backref='User', lazy='dynamic')
    point = db.relationship('Point', backref='User', lazy='dynamic')
    image_service = db.relationship('Image_Service', backref='User', lazy='dynamic')
    log_activity = db.relationship('Log_Activity', backref='User', lazy='dynamic')
