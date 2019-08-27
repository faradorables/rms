from flask import render_template, request, jsonify, redirect, url_for, abort, current_app, \
    send_from_directory, flash
from flask_login import login_required, current_user
from ..models import db, User, Sector
from werkzeug.utils import secure_filename
import pymongo, requests, calendar, os
from datetime import datetime
from sqlalchemy import asc
from bson import ObjectId
from .. import mongo, csrf
from . import tabur_admin
from ..utils import user_log
import xmlrpc.client, requests, time

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg'])


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# @main.route('/google273b4a5af9f9bf98.html')
# def google():
#     return render_template('google273b4a5af9f9bf98.html')

@tabur_admin.route('/tabur/admin-secret/')
def index():
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if current_user.is_anonymous:
        abort(404)
    else:
        if current_user.role_id == 4 and current_user.sector_id != 1:
            abort(404)
        return render_template('main/admin/tabur/index.html')

@tabur_admin.route('/tabur/admin-secret/<sector>')
@login_required
def admin_pages(sector):
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if current_user.is_anonymous:
        abort(404)
    else:
        if current_user.role_id == 4 and current_user.sector_id != 1:
            abort(404)
        if sector not in [
            'home', 'news', 'gallery', 'sector', 'anggota', 'kinerja', 'dpo'
        ]:
            abort(404)
        return render_template('main/admin/tabur/pages/' + sector + '.html')

@tabur_admin.route('/tabur/admin-secret/<sector>/<id>')
@login_required
def _pages(sector, id):
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if current_user.is_anonymous:
        abort(404)
    else:
        if current_user.role_id == 4 and current_user.sector_id != 1:
            abort(404)
        data = None
        if sector == 'data':
            if id == 'kepercayaan':
                data = mongo.db.news.find_one({'_id': ObjectId(id)})
                page = 'data_kepercayaan_pages'
            elif id == 'kepercayaan':
                data = mongo.db.news.find_one({'_id': ObjectId(id)})
                page = 'data_kepercayaan_pages'
            elif id == 'kepercayaan':
                data = mongo.db.news.find_one({'_id': ObjectId(id)})
                page = 'data_kepercayaan_pages'
            else:
                abort(404)
        elif sector == 'news':
            data = mongo.db.news.find_one({'_id': ObjectId(id)})
            page = 'news_pages'
        else:
            abort(404)
        return render_template('main/admin/tabur/pages/' + page + '.html', data=data)


@tabur_admin.route('/tabur/api/v1/admin/home', methods=['POST', 'GET'])
@csrf.exempt
def admin_api_home():
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if request.method == 'POST':
        apidata = request.form
        app = current_app._get_current_object()
        print(apidata)
        response = {}
        user = User.query.filter_by(email=apidata['email']).first()
        if user is not None and user.verify_token(token=apidata['token']):
            sector_id = user.sector_id
            if (user.sector_id == 6 and user.role_id != 4) or user.role_id == 1:
                if apidata['status'] == '0':
                    response['data'] = [{
                        'id': str(i['_id']),
                        'image': i['image']
                    } for i in mongo.db.home.find({'sector_id': 6})]
                    response['count'] = True if mongo.db.home.count({'sector_id': sector_id}) > 0 else False
                    response['status'] = '00'
                elif apidata['status'] == '1':
                    file = request.files['file']
                    print(str(file))
                    if file is not None:
                        if file != '' and allowed_file(file.filename):
                            current_filename = secure_filename(file.filename)
                            filename = str(int(time.time())) + '.' + current_filename.rsplit('.')[1]
                            mongo.db.home.insert({
                                'uploader': user.id,
                                'uploader_name': user.name,
                                'image': filename,
                                'short_desc': None,
                                'sector_id': 6,
                                'timestamp': datetime.utcnow()
                            })
                            file.save(os.path.join(app.config['HOME_UPLOAD_FOLDER'], filename))
                            response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Isi semua field dengan benar.'
                elif apidata['status'] == '2':
                    if len(apidata['id'].strip()) > 0:
                        data = mongo.db.home.find_one({'_id': ObjectId(apidata['id']), 'sector_id': sector_id})
                        response['id'] = str(data['_id'])
                        response['short_desc'] = data['short_desc']
                        response['image'] = data['image']
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Your credential are invalid.'
                elif apidata['status'] == '3':
                    if len(apidata['id'].strip()) > 0 and len(apidata['short_desc'].strip()) > 0:
                        mongo.db.home.update_one({
                            '_id': ObjectId(apidata['id']),
                            'sector_id': 6
                        },{
                            '$set': {
                                'short_desc': apidata['short_desc']
                            }
                        })
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Your credential are invalid.'
            else:
                response['status'] = '50'
                response['message'] = 'Your credential are invalid.'
        else:
            response['status'] = '50'
            response['message'] = 'Your credential are invalid.'
        return jsonify(response)
    else:
        return redirect(url_for('main.index'))

@tabur_admin.route('/tabur/api/v1/admin/news', methods=['POST', 'GET'])
@csrf.exempt
def admin_api_news():
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if request.method == 'POST':
        apidata = request.form
        app = current_app._get_current_object()
        print(apidata)
        response = {}
        user = User.query.filter_by(email=apidata['email']).first()
        if user is not None and user.verify_token(token=apidata['token']):
            if (user.sector_id == 6 and user.role_id != 4) or user.role_id == 1:
                if apidata['status'] == '0':
                    response['data'] = [{
                        'id': str(i['_id']),
                        'title': i['title'],
                        'short_desc': i['short_desc'],
                        'image': i['image'],
                        'timestamp': i['timestamp']
                    } for i in mongo.db.news.find({'sector_id': 6})]
                    response['count'] = True if mongo.db.news.count({'sector_id': 6}) > 0 else False
                    response['status'] = '00'
                elif apidata['status'] == '1':
                    if len(apidata['title'].strip()) > 0 and len(apidata['short_desc'].strip()) > 0 \
                            and len(apidata['description'].strip()) > 0:
                        mongo.db.news.insert({
                            'author_id': user.id,
                            'author_name': user.name,
                            'title': apidata['title'],
                            'short_desc': apidata['short_desc'],
                            'description': apidata['description'],
                            'image': None,
                            'sector_id': 6,
                            'timestamp': datetime.utcnow()
                        })
                        print(apidata)
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Isi semua field dengan benar.'
                elif apidata['status'] == '2':
                    if len(apidata['id'].strip()) > 0:
                        data = mongo.db.news.find_one({'_id': ObjectId(apidata['id']), 'sector_id': 6})
                        response['id'] = str(data['_id'])
                        response['title'] = str(data['title'])
                        response['short_desc'] = str(data['short_desc'])
                        response['description'] = str(data['description'])
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Your credential are invalid.'
                elif apidata['status'] == '3':
                    if len(apidata['id'].strip()) > 0 and len(apidata['title'].strip()) > 0 and len(apidata['short_desc'].strip()) > 0 \
                            and len(apidata['description'].strip()) > 0:
                        if mongo.db.news.count({
                                '_id': ObjectId(apidata['id']),
                                'sector_id': 6,
                            }) > 0:
                            mongo.db.news.update_one(
                                {
                                    '_id': ObjectId(apidata['id']),
                                    'sector_id': 6,
                                }, {
                                    '$set': {
                                        'title': apidata['title'],
                                        'short_desc': apidata['short_desc'],
                                        'description': apidata['description'],
                                    }
                                }
                            )
                            response['status'] = '00'
                        else:
                            response['status'] = '50'
                            response['message'] = 'Data tidak ditemukan.'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Isi semua field dengan benar.'
                elif apidata['status'] == '4':
                    file = request.files['file']
                    print(str(file))
                    if file is not None:
                        if file != '' and allowed_file(file.filename):
                            current_filename = secure_filename(file.filename)
                            filename = str(int(time.time())) + '-' + apidata['id'] + '.' + current_filename.rsplit('.')[1]
                            app = current_app._get_current_object()
                            if mongo.db.news.count({
                                '_id': ObjectId(apidata['id']),
                                'sector_id': 6,
                            }) > 0:
                                mongo.db.news.update(
                                    {
                                        '_id': ObjectId(apidata['id']),
                                        'sector_id': 6,
                                    },
                                    {
                                        '$set': {
                                            'image': filename
                                        }
                                    }
                                )
                                file.save(os.path.join(app.config['NEWS_UPLOAD_FOLDER'], filename))
                            else:
                                response['status'] = '50'
                                response['message'] = 'Data tidak ditemukan.'
            else:
                response['status'] = '50'
                response['message'] = 'Your credential are invalid.'
        else:
            response['status'] = '50'
            response['message'] = 'Your credential are invalid.'
        return jsonify(response)
    else:
        return redirect(url_for('main.index'))

@tabur_admin.route('/tabur/api/v1/admin/gallery', methods=['POST', 'GET'])
@csrf.exempt
def admin_api_gallery():
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if request.method == 'POST':
        apidata = request.form
        app = current_app._get_current_object()
        print(apidata)
        response = {}
        user = User.query.filter_by(email=apidata['email']).first()
        if user is not None and user.verify_token(token=apidata['token']):
            if (user.sector_id == 6 and user.role_id != 4) or user.role_id == 1:
                if apidata['status'] == '0':
                    response['data'] = [{
                        'id': str(i['_id']),
                        'image': i['image']
                    } for i in mongo.db.gallery.find({'sector_id': 6})]
                    response['count'] = True if mongo.db.gallery.count({'sector_id': 6}) > 0 else False
                    response['status'] = '00'
                elif apidata['status'] == '1':
                    file = request.files['file']
                    print(str(file))
                    if file is not None:
                        if file != '' and allowed_file(file.filename):
                            current_filename = secure_filename(file.filename)
                            filename = str(int(time.time())) + '.' + current_filename.rsplit('.')[1]
                            app = current_app._get_current_object()
                            mongo.db.gallery.insert({
                                'uploader': user.id,
                                'uploader_name': user.name,
                                'image': filename,
                                'short_desc': None,
                                'sector_id': 6,
                                'timestamp': datetime.utcnow()
                            })
                            file.save(os.path.join(app.config['GALLERY_UPLOAD_FOLDER'], filename))
                            response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Isi semua field dengan benar.'
                elif apidata['status'] == '2':
                    if len(apidata['id'].strip()) > 0:
                        data = mongo.db.gallery.find_one({'_id': ObjectId(apidata['id']), 'sector_id': 6})
                        response['id'] = str(data['_id'])
                        response['short_desc'] = data['short_desc']
                        response['image'] = data['image']
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Your credential are invalid.'
                elif apidata['status'] == '3':
                    if len(apidata['id'].strip()) > 0 and len(apidata['short_desc'].strip()) > 0:
                        mongo.db.gallery.update_one({
                            '_id': ObjectId(apidata['id']),
                            'sector_id': 6
                        },{
                            '$set': {
                                'short_desc': apidata['short_desc']
                            }
                        })
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Your credential are invalid.'
            else:
                response['status'] = '50'
                response['message'] = 'Your credential are invalid.'
        else:
            response['status'] = '50'
            response['message'] = 'Your credential are invalid.'
        return jsonify(response)
    else:
        return redirect(url_for('main.index'))

@tabur_admin.route('/tabur/api/v1/admin/anggota', methods=['POST', 'GET'])
@csrf.exempt
def admin_api_anggota():
    # ip_list = request.environ['HTTP_X_FORWARDED_FOR']
    # user_log('/', ip_list)
    if request.method == 'POST':
        apidata = request.form
        print(apidata)
        response = {}
        user = User.query.filter_by(email=apidata['email']).first()
        if user is not None and user.verify_token(token=apidata['token']):
            if (user.sector_id == 6 and user.role_id != 4) or user.role_id == 1:
                if apidata['status'] == '0':
                    data_query = User.query.filter(User.sector_id == 6, User.role_id != 4).all()
                    response['data'] = [{
                        'id': i.id,
                        'name': i.name,
                        'image': i.image
                    } for i in data_query]
                    response['sector'] = [{
                        'id': i.id,
                        'name': i.name,
                    } for i in Sector.query.all()]
                    response['count'] = True if User.query.count() > 0 else False
                    response['status'] = '00'
                elif apidata['status'] == '1':
                    if len(apidata['name'].strip()) > 0 and len(apidata['user_email'].strip()) > 0 \
                            and len(apidata['phone_number'].strip()) > 0 and len(apidata['role_id'].strip()) > 0 \
                            and len(apidata['password'].strip()) > 0:
                        if User.query.filter_by(email=request.form['user_email'].lower()).count() != 0:
                            response['status'] = '50'
                            response['message'] = 'Maaf email ini sudah terdaftar.'
                        elif User.query.filter_by(phone_number=request.form['phone_number'].lower()).count() != 0:
                            response['status'] = '50'
                            response['message'] = 'Maaf nomor Handphone ini sudah terdaftar.'
                        else:
                            data = User()
                            data.name = apidata['name']
                            data.email = apidata['user_email']
                            data.phone_number = apidata['phone_number']
                            data.role_id = int(apidata['role_id'])
                            data.sector_id = 6
                            data.password = apidata['password']
                            db.session.add(data)
                            db.session.commit()
                            response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Isi semua field dengan benar.'
                elif apidata['status'] == '2':
                    if len(apidata['id'].strip()) > 0:
                        data = User.query.filter_by(id=apidata['id']).first()
                        response['id'] = data.id
                        response['name'] = data.name
                        response['image'] = data.image
                        response['address'] = data.address
                        response['phone_number'] = data.phone_number
                        response['role_id'] = data.role_id
                        response['email'] = data.email
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Your credential are invalid.'
                elif apidata['status'] == '3':
                    if len(apidata['id'].strip()) > 0 and len(apidata['name'].strip()) > 0 and \
                            len(apidata['address'].strip()) > 0:
                        data = User.query.filter_by(id=apidata['id']).first()
                        data.name = apidata['name']
                        data.address = apidata['address']
                        data.phone_number = apidata['phone_number']
                        data.role_id = int(apidata['role_id'])
                        db.session.commit()
                        response['status'] = '00'
                    else:
                        response['status'] = '50'
                        response['message'] = 'Isi semua field dengan benar.'
                elif apidata['status'] == '4':
                    file = request.files['file']
                    print(str(file))
                    if file is not None:
                        if file != '' and allowed_file(file.filename):
                            current_filename = secure_filename(file.filename)
                            filename = str(int(time.time())) + '-' + apidata['id'] + '.' + current_filename.rsplit('.')[1]
                            app = current_app._get_current_object()
                            mongo.db.information.update(
                                {
                                    '_id': ObjectId(apidata['id'])
                                },
                                {
                                    '$set': {
                                        'image': filename
                                    }
                                }
                            )
                            file.save(os.path.join(app.config['INFO_UPLOAD_FOLDER'], filename))
            else:
                response['status'] = '50'
                response['message'] = 'Your credential are invalid.'
        else:
            response['status'] = '50'
            response['message'] = 'Your credential are invalid.'
        return jsonify(response)
    else:
        return redirect(url_for('main.index'))
