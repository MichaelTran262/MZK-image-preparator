from flask import Blueprint

api = Blueprint('api', __name__)

from . import folder, mzk, processes, prepare, speed