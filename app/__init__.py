from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from config import config
from flask_login import LoginManager
from flask_wtf import CSRFProtect
from flask_pymongo import PyMongo
from flask_pagedown import PageDown
from flask_cors import CORS

bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
mongo = PyMongo()
pagedown = PageDown()
csrf = CSRFProtect()

login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'auth.login'


def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    CORS(app, resources={
        r"/*": {"origins": "*"}
    })

    csrf.init_app(app)
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    mongo.init_app(app)
    login_manager.init_app(app)
    pagedown.init_app(app)

    # attach route and error

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api/v1/ams')

    return app
