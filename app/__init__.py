from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask.logging import default_handler
from celery import Celery, Task
import logging
from config import *

db = SQLAlchemy()

DEBUG = True

def create_app():
    app = Flask(__name__)
    app.config.from_object(LocalDevelopmentConfig())
    db.init_app(app)
    celery_init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .api import api as api_blueprint
    app.register_blueprint(api_blueprint, url_prefix='/api')

    return app

def celery_init_app(app: Flask) -> Celery:
    class FlaskTask(Task):

        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)

    celery = Celery(app.name, task_cls=FlaskTask)
    celery.config_from_object(app.config["CELERY"])
    celery.set_default()
    app.extensions["celery"] = celery
    return celery