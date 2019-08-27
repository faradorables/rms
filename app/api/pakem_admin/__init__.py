from flask import Blueprint

tabur_admin = Blueprint('tabur_admin', __name__)

from . import views