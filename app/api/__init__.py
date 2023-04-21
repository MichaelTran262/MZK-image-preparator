from flask import Blueprint, jsonify
from flask import current_app as app
import os
import threading
from ..dataMover.ProcessMover import ProcessMover

api = Blueprint('api', __name__)

from . import services, processes, folders

@api.route('/send_to_mzk_now/home/<path:req_path>', methods=['POST'])
@api.route('/send_to_mzk_now/<path:req_path>', methods=['POST'])
def api_send_to_mzk_now(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    t = threading.Thread(target=api_create_process_and_run, args=(abs_path, app.config['SMB_USER'], app.config['SMB_PASSWORD'], app._get_current_object()))
    t.daemon = True
    t.start()
    return jsonify({"Status":"ok"}), 200

# Checks whether file already exists at MZK
@api.route('/check_folder_conditions/home/<path:req_path>', methods=['GET'])
@api.route('/check_folder_conditions/<path:req_path>', methods=['GET'])
def check_if_folder_exists(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    return ProcessMover.check_conditions(abs_path, foldername, app.config['SMB_USER'], app.config['SMB_PASSWORD'])


def api_create_process_and_run(src_path, username, password, app):
    mover = ProcessMover(src_path, username, password)
    mover.move_to_mzk_now(app)