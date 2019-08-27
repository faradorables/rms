from flask import render_template, redirect, request, url_for, flash, current_app, \
    send_from_directory, session, app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from ..utils import send_notif
from datetime import datetime, timedelta
from . import auth
from ..models import User, db, Ion_User, Rdb_Plaza, Rdb_Client, Rdb_Lane
from .forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm, ChangePasswordForm, EmailForm
from ..email import send_email
import calendar, os, re
from sqlalchemy import desc, asc
from .. import mongo, csrf
import pdb
import flask_excel as excel

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route('/api/v1/auth/login', methods=['GET', 'POST'])
@csrf.exempt
def request_login():
    if request.method == 'POST':
        response = {}
        response['status'] = '00'
        response['message'] = 'Selamat datang di ION Admin Management System.'
        apidata = request.form
        print(apidata)
        if len(apidata['email']) > 0 and len(apidata['email']) > 0:
            user = Ion_User.query.filter_by(email=apidata['email'], role_id=2).first()
            if user is not None:
                print(user.verify_pin(apidata['pin']))
                if user.verify_pin(apidata['pin']):
                    response['user_id'] = user.id
                    response['token'] = user.generate_token()
                    response['name'] = user.name
                    response['phone_number'] = user.phone_number
                    response['email'] = user.email if user.email != None else '-'
                    login_user(user)
                else:
                    response['status'] = '50'
                    response['message'] = 'The username or password is incorrect'
            else:
                response['status'] = '50'
                response['message'] = 'The username or password is incorrect'
        else:
            response['status'] = '50'
            response['message'] = 'Please fill out all required fields..'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash(u'You have been Logout , Thank you !', 'success')
    return redirect(url_for('main.index'))

@auth.route('/api/v1/add_plaza', methods=['GET', 'POST'])
@csrf.exempt
def _add_plaza():
    if request.method == "POST":
        response = {}
        apidata = request.form
        print(apidata)
        cur_user = Ion_User.query.filter_by(id=apidata['id']).first()
        client = Rdb_Client.query.filter_by(ion_id=apidata['id']).first()
        if cur_user is not None and cur_user.verify_token(apidata['token']):
            Rdb_Plaza()._insert(apidata['name'],client.id,apidata['latitude'],apidata['longitude'],apidata['address'],apidata['image'])
            response['status'] = '00'
            response['messages'] = 'success'
        else:
            response['status'] = '50'
            response['messages'] = 'user tidak terverifikasi'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/api/v1/add_lane', methods=['GET', 'POST'])
@csrf.exempt
def _add_lane():
    if request.method == "POST":
        response = {}
        apidata = request.form
        print(apidata)
        cur_user = Ion_User.query.filter_by(id=apidata['id']).first()
        if cur_user is not None and cur_user.verify_token(apidata['token']):
            Rdb_Lane()._insert(apidata['name'],apidata['lanetype'],apidata['plaza_id'])
            response['status'] = '00'
            response['messages'] = 'success'
        else:
            response['status'] = '50'
            response['messages'] = 'user tidak terverifikasi'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/api/v1/edit_admin', methods=['GET', 'POST'])
@csrf.exempt
def _edit_admin():
    if request.method == "POST":
        response = {}
        apidata = request.form
        print(apidata)
        cur_user = User.query.filter_by(id=apidata['id_admin']).first()
        check_email = User.query.filter_by(email=apidata['email']).first()
        # response['id'] = User()._data(apidata['id'])
        if cur_user is not None and cur_user.verify_token(apidata['token']):
            if check_email is None:
                User()._update(apidata['user_id'],apidata['role'],apidata['name'],apidata['phone'],apidata['email'],apidata['user_id'])
                response['status'] = '00'
                response['messages'] = 'success'
            else:
                response['status'] = '50'
                response['messages'] = 'email sudah ada yang pakai'
        else:
            response['status'] = '50'
            response['messages'] = 'user tidak terverifikasi'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/api/v1/auth/verif_password', methods=['GET', 'POST'])
@csrf.exempt
def verif_password():
    if request.method == 'POST':
        response = {}
        response['status'] = '00'
        response['message'] = 'Password anda sesuai.'
        apidata = request.form
        print(apidata)
        if len(apidata['password']) > 0:
            user = User.query.filter_by(id=apidata['id']).first()
            if user is not None and user.verify_token(apidata['token']):
                if user.verify_password(apidata['password']):
                    response['user_id'] = user.id
                    # response['token'] = user.token
                    login_user(user)
                else:
                    response['status'] = '50'
                    response['message'] = 'The username or password is incorrect'
            else:
                response['status'] = '50'
                response['message'] = 'The username or password is incorrect'
        else:
            response['status'] = '50'
            response['message'] = 'Please fill out all required fields..'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/api/v1/auth/verif_pin', methods=['GET', 'POST'])
@csrf.exempt
def verif_pin():
    if request.method == 'POST':
        response = {}
        response['status'] = '00'
        response['message'] = 'Password anda sesuai.'
        apidata = request.form
        print(apidata)
        if len(apidata['pin']) > 0:
            user = Ion_User.query.filter_by(id=apidata['id']).first()
            if user is not None and user.verify_token(apidata['token']):
                if user.verify_pin(apidata['pin']):
                    response['user_id'] = user.id
                    login_user(user)
                else:
                    response['status'] = '50'
                    response['message'] = 'The username or password is incorrect'
            else:
                response['status'] = '50'
                response['message'] = 'The username or password is incorrect'
        else:
            response['status'] = '50'
            response['message'] = 'Please fill out all required fields..'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/api/v1/upgrade_approval', methods=['GET', 'POST'])
@csrf.exempt
def _upgrade_approval():
    if request.method == "POST":
        response = {}
        apidata = request.form
        print(apidata)
        cur_user = User.query.filter_by(id=apidata['id_admin']).first()
        ion_user = Ion_User.query.filter_by(id=apidata['_user_id']).first()
        if cur_user is not None and cur_user.verify_token(apidata['token']):
            Ion_Upgrade()._upgrade_account(apidata['_user_id'], apidata['_status_upgrade'])
            got_destination = Ion_User.query.filter_by(id=apidata['_user_id'], status=True).first()
            notif_type = Ion_Notification_Type.query.filter_by(id=3).first() #notif type : transaction
            Ion_Notification()._insert(got_destination.id, notif_type.id)
            notif_receiver = Ion_Notification.query.filter_by(user_id=got_destination.id, status=True).all()
            upgrade = Ion_Upgrade.query.filter_by(id=ion_user.id_upgrade).order_by(Ion_Upgrade.id.desc()).first()
            upgrade_status = Ion_Status_Upgrade.query.filter_by(id=upgrade.status_upgrade_id).order_by(Ion_Status_Upgrade.id.desc()).first()
            subject="Upgrade IONCASH"
            if upgrade_status.status_upgrade == 1: #id 1 - status 0 - pending ; #id 2 - status 1 - accept; #id 3 - status 2 - Reject;
                status_upgrade = True
            else: #0 = Pending ; 2 = Reject;
                status_upgrade = False
            count_notif_receiver = len(notif_receiver)
            if int(apidata['_status_upgrade']) == 2:
                header = "Akun anda berhasil ditingkatkan"
                body = "Selamat, akun anda telah berhasil ditingkatkan setelah diverifikasi oleh tim kami. Nikmati fitur transaksi premium yang terdapat pada akun anda"
                response['status'] = '00'
                response['message'] = 'Sukses'
                send_notif(got_destination.firebase_id, header, body, bool(status_upgrade), count_notif_receiver, notif_type.page)
                Ion_Inbox_Upgrade()._insert(subject, body, apidata['_user_id'], 'inbox.png')
            elif int(apidata['_status_upgrade']) == 3:
                header = "Akun anda tidak dapat ditingkatkan"
                body = "Setelah dilakukan verifikasi oleh tim kami, akun anda belum memenuhi kriteria untuk ditingkatkan"
                response['status'] = '00'
                response['message'] = 'Sukses'
                send_notif(got_destination.firebase_id, header, body, bool(status_upgrade), count_notif_receiver, notif_type.page)
                Ion_Inbox_Upgrade()._insert(subject, body, apidata['_user_id'], 'inbox.png')
            else:
                response['status'] = '70'
                response['message'] = 'Error'
        else:
            response['status'] = '50'
            response['messages'] = 'user tidak terverifikasi'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/api/v1/add_client', methods=['GET', 'POST'])
@csrf.exempt
def _add_client():
    if request.method == "POST":
        response = {}
        apidata = request.form
        print(apidata)
        cur_user = User.query.filter_by(id=apidata['id']).first()
        check_email = Ion_User.query.filter_by(email=apidata['email']).first()

        if cur_user.verify_token(apidata['token']):
            if check_email is None:
                Ion_User()._insert_client(apidata['name'],apidata['phone'],apidata['email'], apidata['trxtype'], apidata['pin'])
                response['status'] = '00'
                response['messages'] = 'success'
            else:
                response['status'] = '50'
                response['messages'] = 'email sudah ada yang pakai'
        else:
            response['status'] = '50'
            response['messages'] = 'user tidak terverifikasi'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()

@auth.before_request
def make_session_permanent():
    session.permanent = True

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    return render_template("auth/change_password.html")

@auth.route('/request/auth-change-password', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def request_change_password():
    if request.method == 'POST':
        response = {}
        response['status'] = 1
        response['message'] = 'Password anda telah diubah'
        if current_user.verify_password(apidata['old_password']):
            if apidata['password'] != apidata['password2']:
                response['status'] = 0
                response['message'] = 'Password yang anda masukkan tidak sama'
            else:
                if len(apidata['password']) < 8:
                    response['status'] = 0
                    response['message'] = 'Password anda terdiri kurang dari 8 karakter'
                else:
                    if re.search(r"[a-z{1,9}]", apidata['password']) is None \
                            or re.search(r"\d{1,5}", apidata['password']) is None \
                            or re.search(r"[A-Z{1,5}]", apidata['password']) is None:
                        response['status'] = 2
                        response['message'] = 'Password anda terdiri kurang dari 8 karakter'
                    else:
                        current_user.password = apidata['password']
                        db.session.add(current_user)
                        db.session.commit()
        else:
            response['status'] = 0
            response['message'] = 'Password lama yang anda masukkan tidak benar'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))

@auth.route('/change-pin', methods=['GET', 'POST'])
@login_required
def change_pin():
    return render_template("auth/change_pin.html")

@auth.route('/request/auth-change-pin', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def request_change_pin():
    if request.method == 'POST':
        response = {}
        response['status'] = 1
        response['message'] = 'Pin anda telah diubah'
        print(apidata)
        if current_user.verify_pin(apidata['old_password']):
            if apidata['password'] != apidata['password2']:
                response['status'] = 0
                response['message'] = 'Pin yang anda masukkan tidak sama'
            else:
                if len(apidata['password']) < 6:
                    response['status'] = 0
                    response['message'] = 'Pin anda terdiri kurang dari 6 karakter'

                else:
                    current_user.pin_hash = apidata['password']
                    db.session.add(current_user)
                    db.session.commit()
        else:
            response['status'] = 0
            response['message'] = 'Password lama yang anda masukkan tidak benar'
        return jsonify(response)
    else:
        return redirect(url_for('.index'))
