import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy


class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://fkn_att2:fkn_att2@localhost/fkn_att2?auth_plugin=mysql_native_password"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False # Autocommit
    SQLALCHEMY_TRACK_MODIFICATIONS = False # ??? Если не прописать, то будет Warning


app = Flask(__name__)
app.config.from_object(Config())
app.config['SECRET_KEY'] = os.urandom(24)
db = SQLAlchemy(app=app, session_options={'autoflush':False})
