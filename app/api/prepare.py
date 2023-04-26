from flask import jsonify, request, g, url_for
from flask import current_app as app
from .. import db, socketIo
from . import api
import os
import threading
from ..preparator.Preparator import Preparator

@api.route('/prepare/check_folder_condition/home/<path:req_path>', methods=['GET', 'POST'])
@api.route('/prepare/check_folder_condition/<path:req_path>', methods=['GET', 'POST'])
def prepare_check_folder_conditions(req_path):
    print(req_path)
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    print(abs_path)
    conditions = Preparator.check_condition(abs_path)
    return conditions, 200

@api.route('/prepare/prepare_folder/home/<path:req_path>', methods=['POST'])
@api.route('/prepare/prepare_folder/<path:req_path>', methods=['POST'])
def prepare_prepare_folders(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    msg = Preparator.prepare_folder(app.config['SRC_FOLDER'], app, req_path)
    print(msg)
    return jsonify({"Status":"ok"}), 200

