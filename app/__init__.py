from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.logging import default_handler
import logging
from .main import main as main_blueprint
from app.dataMover.Utility import Utility
from app.dataMover.Database import db

app = Flask(__name__)

DEBUG = True

def create_app():
    app = Flask(__name__)
    URL = 'postgresql://{username}:{password}@192.168.80.2:{port}/{dbName}' \
        .format(
            username='postgres',
            password='password',
            dbName='baseddata',
            port='5432'
        )
    app.config.update(
    SQLALCHEMY_DATABASE_URI = URL
    )
    db.init_app(app)
    if DEBUG: 
        logger = logging.getLogger('werkzeug')
    else:
        logger = logging.getLogger('gunicorn.access')
    #fh = logging.FileHandler('/logs/preparator.log', 'a', 'utf-8')
    #logger.addHandler(fh)
    app.logger.addHandler(logger)
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)
    return app


