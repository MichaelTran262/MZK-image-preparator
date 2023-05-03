from flask import jsonify, request, g, url_for
from flask import current_app as app
from celery import shared_task
from .. import db, socketIo
from ..models import ProcessDb
from . import api
import os
import threading
from ..dataMover.DataMover import DataMover

@api.route('/send_to_mzk_now/home/<path:req_path>', methods=['POST'])
@api.route('/send_to_mzk_now/<path:req_path>', methods=['POST'])
def api_send_to_mzk_now(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    r = api_create_process_and_run.delay(abs_path, app.config['SMB_USER'], app.config['SMB_PASSWORD'])
    return jsonify({"Status" : "ok", "task_id" : r.task_id}), 200

# Checks whether file already exists at MZK
@api.route('/check_folder_conditions/home/<path:req_path>', methods=['GET'])
@api.route('/check_folder_conditions/<path:req_path>', methods=['GET'])
def check_if_folder_exists(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    return DataMover.check_conditions(abs_path, foldername, app.config['SMB_USER'], app.config['SMB_PASSWORD'])

@shared_task(ignore_results=False)
def api_create_process_and_run(src_path, username, password):
    mover = DataMover(src_path, username, password)
    mover.move_to_mzk_now()