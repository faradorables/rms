from app import db
from werkzeug.security import generate_password_hash,check_password_hash
from sqlalchemy import func
from flask_login import UserMixin, current_user
from app import db,login_manager
from . import mongo
import pymongo, requests
from .utils import *
from flask import jsonify, session
from calendar import monthrange
import pandas as pd

@login_manager.user_loader
def load_user(user_id):
    return user.query.get(user_id)    

class user(db.Model,UserMixin):
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
        insert = user()
        insert.name = _name
        insert.phone_number = _phonenumber
        insert.password_hash = generate_password_hash(_password)
        insert.pin_hash = None
        insert.email = _email
        insert.outlet_id = None
        insert.role_id = _role
        insert.address = _address
        insert.gender_id = _gender
        insert.birthdate =_birthdate
        insert.add_time = datetime.now()
        db.session.add(insert)
        db.session.commit()
        return insert

    def _updateowner(self, _id, _name, _phonenumber, _email, _role, _address, _gender, _birthdate):
        update = user()
        update = user.query.filter_by(id=_id).first()
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
        insert = user()
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
        update = user()
        update = user.query.filter_by(id=_id).first()
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
        remove = user()
        remove = user.query.filter_by(id = _id).first()
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
        _user = user.query.filter_by(id = _id, status = True).first()
        if _user is not None:
            response['id'] =  _user.id 
            response['name'] =  _user.name
            response['phone_number'] =  _user.phone_number
            response['email'] =  _user.email
            response['outlet_id'] =  _user.outlet_id
            response['role_id'] =  _user.role_id
        return response
        
    def _list(self):
        response = {}
        response['data'] = []
        _user = user.query.filter_by(status = True).all()
        for i in _user:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name ,
                'phone_number' : i.phone_number,
                'email' : i.email,
                'birthdate' : i.birthdate.strftime("%m-%d-%Y"),
                'address' : i.address,
                'role' : role()._data(i.role_id),
                'outlet' : outlet()._data(i.outlet_id)
            })
        return response

class outlet(db.Model,UserMixin):
    __tablename__ = 'outlet'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.Text)
    user_id = db.Column(db.Integer,db.ForeignKey('user.id'))
    email = db.Column(db.String(100),index=True)
    phone_number = db.Column(db.String(50),index=True)
    address = db.Column(db.Text)
    m_category = db.Column(db.Integer,db.ForeignKey('m_category.id'))
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

    def _insert(self, _name, _userid, _email, _phonenumber, _address, _category, _province, _city, _kecamatan, _kelurahan,  _postalcode, _rt, _rw, _statusaddress):
        insert = outlet()
        insert.name = _name
        insert.user_id = _userid
        insert.email = _email
        insert.phone_number = _phonenumber
        insert.address = _address
        insert.m_category = _category
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

    
    def _update(self, _id, _name, _userid, _email, _phonenumber, _address, _category, _province, _city, _kecamatan, _kelurahan,  _postalcode, _rt, _rw, _statusaddress):
        update = outlet()
        update = outlet.query.filter_by(id=_id).first()
        update.name = _name
        update.user_id = _userid
        update.email = _email
        update.phone_number = _phonenumber
        update.address = _address
        update.m_category = _category
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
        remove = outlet()
        remove = outlet.query.filter_by(id = _id).first()
        remove.status = False
        db.session.add(remove)
        db.session.commit()

    def _data(self,_id):
        response = {}
        _outlet = outlet.query.filter_by(id = _id, status = True).first()
        if _outlet is not None:
            response['id'] =  _outlet.id 
            response['name'] =  _outlet.name
            response['email'] =  _outlet.email
            response['address'] =  _outlet.address
        return response
    
    def _list(self):
        response = {}
        response['data'] = []
        _outlet = outlet.query.filter_by(status = True).all()
        for i in _outlet:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name,
                'email' : i.email,
                'address' : i.address,
                'phone_number' : i.phone_number
            })
        return response

class m_category(db.Model,UserMixin):
    __tablename__ = 'm_category'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name):
        insert = m_category()
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name):
        update = m_category()
        update = m_category.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = m_category()
        update = m_category.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _m_category = m_category.query.filter_by(status = True)).all()
        for i in _province:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name
            })
        return response
    
    def _data(self, _id):
        response = {}
        _m_category = m_category.query.filter_by(id = _id, status = True).first()
        if _m_category is not None:
            response['id'] = _m_category.id 
            response['name'] = _m_category.name 
        return response

class province(db.Model,UserMixin):
    __tablename__ = 'province'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name):
        insert = province()
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name):
        update = province()
        update = province.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = province()
        update = province.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _province = province.query.filter_by(status = True).order_by(province.name.asc()).all()
        for i in _province:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name 
            })
        return response
    
    def _data(self, _id):
        response = {}
        _province = province.query.filter_by(id = _id, status = True).first()
        if _province is not None:
            response['id'] = _province.id 
            response['name'] = _province.name 
        return response

class city(db.Model,UserMixin):
    __tablename__ = 'city'

    id = db.Column(db.Integer,primary_key=True)
    province_id = db.Column(db.Integer,db.ForeignKey('province.id'))
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _province):
        insert = city()
        insert.province_id = _province
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _province):
        update = city()
        update = city.query.filter_by(id = _id).first()
        update.province_id = _province
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = city()
        update = city.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self, _id):
        response = {}
        response['data'] = []
        _city = city.query.filter_by(province_id = _id).filter_by(status = True).order_by(city.name.asc()).all()
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
        _city = city.query.filter_by(status = True).all()
        for i in _city:
            response['data'].append({
                'id' : i.id,
                'province_id' : i.province_id,
                'name' : i.name 
            })
        return response

    def _data(self,_id):
        response = {}
        _city = city.query.filter_by(id = _id).filter_by(status = True).first()
        if _city is not None:
            response['id'] = _city.id
            response['province_id'] = _city.province_id
            response['name'] = _city.name
        return response

class district(db.Model,UserMixin):
    __tablename__ = 'district'

    id = db.Column(db.Integer,primary_key=True)
    city_id = db.Column(db.Integer,db.ForeignKey('city.id'))
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _city):
        insert = district()
        insert.city_id = _city
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _idcity):
        update = district()
        update = district.query.filter_by(id = _id).first()
        update.city_id = _idcity
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = district()
        update = district.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self,_id):
        response = {}
        response['data'] = []
        _kecamatan = district.query.filter_by(city_id = _id).filter_by(status = True).order_by(kecamatan.name.asc()).all()
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
        _kecamatan = district.query.filter_by(status = True).all()
        for i in _kecamatan:
            response['data'].append({
                'id' : i.id,
                'city_id' : i.city_id,
                'name' : i.name 
            })
        return response
    def _data(self, _id):
        response = {}
        _kecamatan = district.query.filter_by(id = _id).filter_by(status = True).first()
        if _kecamatan is not None:
            response['id'] = _kecamatan.id
            response['city_id'] = _kecamatan.city_id
            response['name'] = _kecamatan.name 
        return response

class sub_district(db.Model,UserMixin):
    __tablename__ = 'sub_district'

    id = db.Column(db.String(20),primary_key=True)
    district_id = db.Column(db.Integer,db.ForeignKey('district.id'))
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _kecamatan):
        insert = sub_district()
        insert.kecamatan_id = _kecamatan
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _kecamatan):
        update = sub_district()
        update = sub_district.query.filter_by(id = _id).first()
        update.name = _name
        update.kecamatan_id = _kecamatan
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = sub_district()
        update = sub_district.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self,_id):
        response = {}
        response['data'] = []
        _kelurahan = sub_district.query.filter_by(kecamatan_id = _id).filter_by(status = True).order_by(sub_district.name.asc()).all()
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
        _kelurahan = sub_district.query.filter_by(status = True).all()
        for i in _kelurahan:
            response['data'].append({
                'id' : i.id,
                'kecamatan_id' : i.kecamatan_id,
                'name' : i.name 
            })
        return response
    
    def _data(self,_id):
        response = {}
        _kelurahan = sub_district.query.filter_by(id = _id).filter_by(status = True).first()
        if _kelurahan is not None:
            response['id'] = _kelurahan.id
            response['kecamatan_id'] = _kelurahan.kecamatan_id
            response['name'] = _kelurahan.name 
        return response

class postal_code(db.Model,UserMixin):
    __tablename__ = 'postal_code'

    id = db.Column(db.Integer,primary_key=True)
    sub_district_id = db.Column(db.String(20),db.ForeignKey('sub_district.id'))
    name = db.Column(db.String(6))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name, _kelurahan):
        insert = postal_code()
        insert.kelurahan_id = _kelurahan
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name, _kelurahan):
        update = postal_code()
        update = postal_code.query.filter_by(id = _id).filter_by(status = True).first()
        upadte.kelurahan_id = _kelurahan
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = postal_code()
        update = postal_code.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self,_kelurahan):
        response = {}
        response['data'] = []
        _postalcode = postal_code.query.filter_by(status = True, kelurahan_id = _kelurahan).all()
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
        _postalcode = postal_code.query.filter_by(status = True).all()
        for i in _postalcode:
            response['data'].append({
                'id' : i.id,
                'kelurahan_id' : i.kelurahan_id,
                'name' : i.name 
            })
        return response

    def _data(self,_id):
        response = {}
        _postalcode = postal_code.query.filter_by(id = _id).filter_by(status = True).first()
        if _postalcode is not None:
            response['id'] = _postalcode.id
            response['kelurahan_id'] = _postalcode.kelurahan_id
            response['name'] = _postalcode.name 
        return response
 
class category(db.Model,UserMixin):
    __tablename__ = 'category'

    id = db.Column(db.Integer,primary_key=True)
    outlet_id = db.Column(db.Integer,db.ForeignKey('outlet.id'))
    name = db.Column(db.Text)
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_userid, _amount):
        insert = category()
        insert.user_id = _userid
        insert.amount = _amount  
        insert.add_time = datetime.now()      
        db.session.add(insert)
        db.session.commit()

    def _update(self, _id, _amount):
        update = category()
        update = category.query.filter_by(id = _id).first()
        update.amount = _amount
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = category()
        update = category.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()
        
    def _data(self, _userid):
        response = {}
        _salary = category.query.filter_by(user_id = _userid).filter_by(status = True).first()
        if _salary is not None:
            response['id'] = _salary.id
            response['user_id'] = _salary.user_id
            response['amount'] = _salary.amount 
        return response

class price(db.Model,UserMixin):
    __tablename__ = 'price'

    id = db.Column(db.Integer,primary_key=True)
    item_id = db.Column(db.Integer,db.ForeignKey('item_detail.id'))
    value = db.Column(db.String(100))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _itemid, _value):
        insert = price()
        insert.item_id = _itemid  
        insert.value = _value  
        insert.add_time = datetime.now()   
        db.session.add(insert)
        db.session.commit()

    def _update(self, _id, _name):
        update = price()
        update = price.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()
    
    def _remove(self, _id):
        update = price()
        update = price.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()
        
    def _list(self):
        response = {}
        response['data'] = []
        _division = price.query.filter_by(status = True).all()
        for i in _division:
            response['data'].append({
                'id' : i.id,
                'name' : i.name
            })
        return response

    def _data(self, _id):
        response = {}
        _division = price.query.filter_by(id = _id, status = True).first()
        if _division is not None:
            response['id'] = _division.id
            response['name'] = _division.name
        return response

    def _getlast(self, _id):
        response = {}
        _price = price.query.filter_by(item_id = _id, status = True).first()
        if _price is not None:
            response['id'] = _price.id
            response['value'] = _price.value
        return response

class tax(db.Model,UserMixin):
    __tablename__ = 'tax'

    id = db.Column(db.Integer,primary_key=True)
    outlet_id = db.Column(db.Integer,db.ForeignKey('outlet.id'))
    value = db.Column(db.String(100))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _outletid, _value):
        insert = tax()
        insert.outlet_id = _outletid
        insert.value = _value  
        insert.add_time = datetime.now()  
        db.session.add(insert)
        db.session.commit()

    def _update(self,_id, _outletid, _value):
        update = tax()
        update = tax.query.filter_by(id = _id).first()
        update.outlet_id = _outletid
        update.value = _value  
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = tax()
        update = tax.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _position = tax.query.filter_by(status = True).all()
        for i in _position:
            response['data'].append({
                'id' : i.id
            })
        return response 
    
    def _data(self, _userid):
        response = {}
        _position = tax.query.filter_by(user_id = _userid).filter_by(status = True).first()
        if _position is not None:
            response['id'] = _position.id
        return response        

class item_detail(db.Model,UserMixin):
    __tablename__ = 'item_detail'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    category_id = db.Column(db.Integer,db.ForeignKey('category.id'))
    outlet_id = db.Column(db.Integer,db.ForeignKey('outlet.id'))
    description = db.Column(db.Text)
    purchase_item = db.Column(db.Boolean,default=False)
    composed_item = db.Column(db.Boolean,default=False)
    sold_item = db.Column(db.Boolean,default=True)
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _name, _category, _outlet, _description):
        insert = item_detail()
        insert.name = _name   
        insert.category_id = _category  
        insert.outlet_id = _outlet     
        insert.description = _description  
        insert.add_time = datetime.now()   
        db.session.add(insert)
        db.session.commit()
        return insert

    def _update(self, _id, _name, _category, _outlet, _description):
        update = item_detail()
        update = item_detail.query.filter_by(id = _id).first()  
        update.name = _name   
        update.category_id = _category  
        update.outlet_id = _outlet     
        update.description = _description  
        db.session.add(update)
        db.session.commit()
    
    def _remove(self, _id):
        update = item_detail()
        update = item_detail.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _itemdetail = item_detail.query.filter_by(status = True).all()
        for i in _itemdetail:
            response['data'].append({
                'id' : i.id,
                'name' : i.name,
                'category_id' : i.category_id,
                'outlet_id' : i.outlet_id,
                'description' : i.description,
                'price' : price()._getlast(i.id)
            })
        return response 

    def _data(self, _id):
        response = {}
        _itemdetail = item_detail.query.filter_by(id = _id, status = True).first()
        if _itemdetail is not None:
            response['id'] = _itemdetail.id
            response['name'] = _itemdetail.name
            response['category_id'] = _itemdetail.category_id
            response['outlet_id'] = _itemdetail.outlet_id
            response['description'] = _itemdetail.description
        return response 

class payment_type(db.Model,UserMixin):
    __tablename__ = 'payment_type'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _name, _uid):
        insert = payment_type()
        insert.name = _name   
        insert.add_time = datetime.now()     
        db.session.add(insert)
        db.session.commit()

    def _update(self, _id, _name, _uid):
        update = payment_type()
        update = payment_type.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _remove(self, _id):
        update = payment_type()
        update = payment_type.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _bank_list = payment_type.query.filter_by(status = True).all()
        for i in _bank_list:
            response['data'].append({
                'id' : i.id,
                'name' : i.name
            })
        return response 
    
    def _data(self, _id):
        response = {}
        _bank_list = payment_type.query.filter_by(id = _id).filter_by(status = True).first()
        if _bank_list is not None:
            response['id'] = _bank_list.id
            response['name'] = _bank_list.name
        return response 

class payment_name(db.Model,UserMixin):
    __tablename__ = 'payment_name'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    type_id = db.Column(db.Integer,db.ForeignKey('payment_type.id'))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _userid, _amount):
        insert = payment_name()
        insert.user_id = _userid  
        insert.amount = _amount
        insert.add_time = datetime.now()  
        db.session.add(insert)
        db.session.commit()

    def _update(self, _id, _amount):
        update = payment_name()
        update = payment_name.query.filter_by(id = _id).first()
        update.amount = _amount
        db.session.add(update)
        db.session.commit()
    
    def _remove(self, _id):
        update = payment_name()
        update = payment_name.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _data(self, _userid):
        response = {}
        _overtime = payment_name.query.filter_by(user_id = _userid).filter_by(status = True).first()
        if _overtime is not None:
            response['id'] = _overtime.id
            response['user_id'] = _overtime.user_id
            response['amount'] = _overtime.amount
        return response 
    
class role(db.Model,UserMixin):
    __tablename__ = 'role'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(100))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self, _name):
        insert = role()
        insert.name = _name  
        insert.add_time = datetime.now()  
        db.session.add(insert)
        db.session.commit()

    def _update(self, _id, _name):
        update = role()
        update = role.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()
    
    def _remove(self, _id):
        update = role()
        update = role.query.filter_by(id = _id).first()
        update.status = False
        db.session.add(update)
        db.session.commit()

    def _data(self, _id):
        response = {}
        _role = role.query.filter_by(id = _id).filter_by(status = True).first()
        if _role is not None:
            response['id'] = _role.id
            response['name'] = _role.name
        return response 

    def _list(self):
        response = {}
        response['data'] = []
        _role = role.query.filter_by(status = True).all()
        for i in _role:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name 
            })
        return response
        
class list_status_address(db.Model,UserMixin):
    __tablename__ = 'list_status_address'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(50))
    add_time = db.Column(db.DateTime,default=datetime.utcnow)
    status = db.Column(db.Boolean,default=True)

    def _insert(self,_name):
        insert = list_status_address()
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name):
        update = list_status_address()
        update = list_status_address.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _statusaddress = list_status_address.query.filter_by(status = True).all()
        for i in _statusaddress:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name 
            })
        return response
    
    def _data(self, _id):
        response = {}
        _statusaddress = list_status_address.query.filter_by(id = _id, status = True).first()
        if _statusaddress is not None:
            response['id'] = _statusaddress.id 
            response['name'] = _statusaddress.name 
        return response

class list_template(db.Model,UserMixin):
    __tablename__ = 'list_template'

    id = db.Column(db.Integer,primary_key=True)
    templatename = db.Column(db.String(100))
    templatelocation = db.Column(db.String(100))

    def _insert(self,_name):
        insert = list_template()
        insert.name = _name
        insert.add_time = datetime.now()
        db.session.add(insert)

    def _update(self, _id, _name):
        update = list_template()
        update = list_template.query.filter_by(id = _id).first()
        update.name = _name
        db.session.add(update)
        db.session.commit()

    def _list(self):
        response = {}
        response['data'] = []
        _statusaddress = list_template.query.filter_by(status = True).all()
        for i in _statusaddress:
            response['data'].append({
                'id' : i.id ,
                'name' : i.name 
            })
        return response
    
    def _data(self, _name):
        response = {}
        _statusaddress = list_template.query.filter_by(templatename = _name).first()
        if _statusaddress is not None:
            response['location'] = _statusaddress.templatelocation 
        return response

class gender(db.Model,UserMixin):
    __tablename__ = 'gender'

    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.Text)

    def _insert(self, _name):
        insert = gender()
        insert.name = _name
        db.session.add(insert)
        db.session.commit()

    def _data(self,_id):
        response = {}
        _gender = gender.query.filter_by(id = _id).first()
        if _gender is not None:
            response['id'] =  _gender.id 
            response['name'] =  _gender.name
        return response

class trx_log:
    kasir_id = None
    outlet_id = None
    list_item = {
        'item_id' : None,
        'quantity' : None
    }
    list_tax = {
        'tax_id'
    }
    sub_total = None
    Total = None
    status_trx = None
    added_time = datetime.now()

    def _insertlog(self, _userid, _walletid, _typeid, _typename, _phone, _name, _transtype, _descrip, _amount, _status):
        response = {}
        _data_ = {}
        if _userid != None:
            _data_['user_id'] = _userid
            _data_['wallet_id'] = _walletid
            _data_['type_id'] = _typeid
            _data_['type_name'] = _typename
            _data_['timestamp'] = self.timestamp
            _data_['_provider_id'] = 'ION'
            _data_['_phone'] = _phone
            _data_['_name'] = _name
            _data_['_Transtype'] = _transtype
            _data_['_description'] = _descrip
            _data_['_amount'] = _amount
            _data_['_status'] = _status
            mongo.db.trx_log.insert(_data_) #melakukan insert data ke mongodb
        else:
            response['status'] = '50'
            response['messages'] = 'User Id tidak ada'

    def _list(self, user_id):
        response = {}
        response['data'] = []   
        limit = 10
        for i in mongo.db.trx_log.find({'user_id' : user_id}):
            response['data'].append({
                'id': str(i['_id']),
                'user_id' : i['user_id'],
                'name': i['_name'],
                'phone': i['_phone'],
                'status': i['_status'],
                'amount': i['_amount'],
                'timestamp': str(i['timestamp']).replace('GMT', '').strip()
            })
        return response

def reinit():
    db.drop_all()
    db.create_all()

def ifnull(var):
  if var is None:
    return var
  return var.strftime("%Y-%m-%d")