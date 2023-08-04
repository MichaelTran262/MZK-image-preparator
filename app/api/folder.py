from flask import jsonify, request
from flask import current_app as flask_app
from celery import shared_task
from celery import current_app as celery_app
from ..models import ProcessDb
from ..dataMover.DataMover import DataMover
from . import api
import os


# Checks whether file already exists at MZK
@api.route('/folder/mzk/conditions/home/<path:req_path>', methods=['GET'])
@api.route('/folder/mzk/conditions/<path:req_path>', methods=['GET'])
def check_if_folder_exists(req_path):
    """
    Checks, whether the folder exists at mzk
    """
    abs_path = os.path.join(flask_app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    conditions = DataMover.check_conditions(abs_path, foldername)
    conditions['active'] = DataMover.get_active_count(celery_app)
    return conditions


@api.route('/folder/mzk/<folder_name>', methods=['GET'])
def is_folder_at_mzk(folder_name):
    '''
    Checks whether folder is at mzk, it is used just for checking whether folder is at MZK
    '''
    result = DataMover.search_dst_folders(folder_name)
    return jsonify({'folder': folder_name, 'result': result})


@api.route('/folder/mzk/progress/', methods=['GET'])
def send_to_mzk_progress():
    '''
    Checks progress of folder
    '''
    src_path = request.args.get('src_path', default=None)
    dst_path = request.args.get('dst_path', default=None)
    if not src_path or not dst_path:
        return jsonify({'message': 'Error: src_path or dst_path is empty'})
    total = 0
    try:
        for path, subdirs, files in os.walk(src_path):
            total += len(files)
    except Exception as e:
        return 0, 0
    total_space = DataMover.get_folder_size(src_path)
    current, current_space = DataMover.get_folder_progress(dst_path=dst_path)
    return jsonify({'current_files':current, 'total_files': total, 'current_space': current_space, 'total_space': total_space}), 200


# Is it better to send path in json instead of baking the path into endpoint?
@api.route('/folder/mzk/send/home/<path:req_path>', methods=['POST'])
@api.route('/folder/mzk/send/<path:req_path>', methods=['POST'])
def api_send_to_mzk(req_path):
    '''
    Moves files from abs_path to dst_folder
    '''
    abs_path = os.path.join(flask_app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    try:
        dst_path = request.get_json()['dst_folder']
    except Exception as e:
        flask_app.logger.error(e)
        return jsonify({"Status" : "ERROR", "message": "dst_folder is empty or invalid"}), 400
    r = api_create_process_and_run.delay(abs_path, dst_path, flask_app.config['SMB_USER'], flask_app.config['SMB_PASSWORD'])
    src_path = abs_path + '/2' #, "task_id" : r.task_id
    dst_path2 = '/mnt/MZK' + dst_path + '/' + foldername
    return jsonify({"Status" : "ok", "task_id" : r.task_id, "src_path": src_path, "dst_path": dst_path2}), 200


# Is it better to send path in json instead of baking the path into endpoint?
'''
TODO: 
1. Check if there is a process instance with future time
'''
@api.route('/folder/mzk/send-later/home/<path:req_path>', methods=['POST'])
@api.route('/folder/mzk/send-later/<path:req_path>', methods=['POST'])
def api_send_later_to_mzk(req_path):
    abs_path = os.path.join(flask_app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    try:
        dst_path = request.get_json()['dst_folder']
    except Exception as e:
        flask_app.logger.error(e)
        return jsonify({"Status" : "ERROR", "message": "dst_folder is empty or invalid"}), 400
    r = api_create_process.delay(abs_path, foldername, dst_path)
    return jsonify({"Status" : "ok"}), 200


@api.route('/folder/mzk/send-later/conditions/home/<path:req_path>', methods=['GET'])
@api.route('/folder/mzk/send-later/conditions/<path:req_path>', methods=['GET'])
def api_send_later_conditions(req_path):
    '''
    Check conditions for planned process folder
    '''
    abs_path = os.path.join(flask_app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    if ProcessDb.is_planned_running():
        return({"planned_running": True, "exists_in_process": True})
    proc = ProcessDb.get_planned_process()
    if proc:
        for proc_folder in proc.folders:
            flask_app.logger.debug("Process " + str(proc.id) + " has folder with path " + proc_folder.folder_name)
            if foldername == proc_folder.folder_name:
                return jsonify({"planned_running": False,"exists_in_process": True})
    return jsonify({"planned_running": False, "exists_in_process": False})


@shared_task(ignore_results=False, bind=True)
def api_create_process_and_run(self, src_path, dst_path, username, password):
    """
    Used for send now
    """
    foldername = os.path.split(src_path)[1]
    mover = DataMover(src_path=src_path, dst_path=dst_path, username=username, password=password)
    process = mover.create_process(foldername=foldername, planned=False)
    ProcessDb.set_celery_task_id(process.id, self.request.id)
    ProcessDb.set_process_to_started(process.id)
    mover.move_to_mzk_now(process=process)


@shared_task(ignore_results=False, bind=True)
def api_create_process(self, src_path, foldername, dst_path):
    """
    Used for send later
    """
    username, password = flask_app.config['SMB_USER'], flask_app.config['SMB_PASSWORD']
    mover = DataMover(src_path=src_path, dst_path=dst_path, username=username, password=password)
    mover.create_process(foldername, True)