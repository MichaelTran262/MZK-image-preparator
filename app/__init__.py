from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.logging import default_handler
import logging
from app.Utility import Utility


app = Flask(__name__)
#db = SQLAlchemy()

DEBUG = True

def create_app():
    app = Flask(__name__)
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app


