from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.logging import default_handler
import logging
from config import DevelopmentConfig

app = Flask(__name__)
db = SQLAlchemy()

DEBUG = True

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevelopmentConfig())
    db.init_app(app)
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app


