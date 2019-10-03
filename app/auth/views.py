from flask import render_template, redirect, request, url_for, flash, current_app, \
    send_from_directory, session, app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from ..utils import send_notif
from datetime import datetime, timedelta
from . import auth
from ..models import User, db
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
            user = User.query.filter_by(email=apidata['email']).first()
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

@auth.route('/api/v1/add_admin', methods=['GET', 'POST'])
@csrf.exempt
def _add_admin():
    if request.method == "POST":
        response = {}
        apidata = request.form
        print(apidata)
        cur_user = User.query.filter_by(id=apidata['id']).first()
        check_email = User.query.filter_by(email=apidata['email']).first()

        if cur_user.verify_token(apidata['token']):
            if check_email is None:
                User()._insert(apidata['name'],apidata['phone'],apidata['email'],apidata['password'],apidata['pin'], apidata['role'])
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
