from flask import Flask
from flask_sqlalchemy import SQLAlchemy


class Config:
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = "mysql+mysqlconnector://fkn_att2:fkn_att2@localhost/fkn_att2?auth_plugin=mysql_native_password"
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False # Autocommit
    SQLALCHEMY_TRACK_MODIFICATIONS = False # ??? Если не прописать, то будет Warning
    SECRET_KEY = 'tsVb&kIvXW9$*hM2XM@XsGo'


app = Flask(__name__)
app.config.from_object(Config())
db = SQLAlchemy(app=app, session_options={'autoflush':False})
