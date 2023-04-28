from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask.logging import default_handler
import logging
from config import *

db = SQLAlchemy()
socketIo = SocketIO() 

DEBUG = True

def create_app():
    app = Flask(__name__)
    app.config.from_object(ProductionConfig())
    db.init_app(app)
    socketIo.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')
    return app


