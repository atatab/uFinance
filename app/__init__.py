from flask import Flask
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__,static_url_path='')
app.secret_key = '76966e024238370e7fb9472e964b3b95'

app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///app_db.db"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = "/home/crmoura93/uFinance/app/static/uploads/transactions_attachments"
db = SQLAlchemy(app)

from app.controllers import *
from app.models import *

@login_manager.user_loader
def user_loader(user_id):
    return User.query.get(user_id)
