from flask import render_template, request, jsonify, redirect, url_for, abort, current_app, \
    send_from_directory, flash
from flask_login import login_required, current_user
from ..models import db, User
from werkzeug.utils import secure_filename
import pymongo, requests, calendar, os
from datetime import datetime, timedelta
from sqlalchemy import asc
from bson import ObjectId
from .. import mongo
from . import main
from .Q import user_log
from .product import prabayar_topup
import xmlrpc.client, requests, time

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @main.route('/google273b4a5af9f9bf98.html')
# def google():
#     return render_template('google273b4a5af9f9bf98.html')

@main.route('/')
def index():
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if current_user.is_authenticated:
        return render_template('main/user/index.html')
    return render_template('main/index.html')

@main.route('/page/<sector>')
@login_required
def _page(sector):
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if sector not in ['dashboard','users', 'admin', 'outlet']:
        abort(404)
    return render_template('main/user/' + sector + '/index.html')
