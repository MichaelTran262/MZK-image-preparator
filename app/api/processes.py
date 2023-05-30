from flask import jsonify, request, g, url_for, redirect, abort, render_template
from flask import current_app as app
from celery import shared_task
from celery import current_app as celery_app
from celery.result import AsyncResult
from ..models import ProcessDb
from ..dataMover.DataMover import DataMover
from . import api
import os


@api.route('/processes', methods=['GET'])
def get_processes_api():
    page = request.args.get('page', 1, type=int)
    procs = ProcessDb.get_processes_by_page(page)
    result = []
    if procs is None:
        abort(404)
    for proc in procs:
        dict = proc.to_json()
        dict['state'] = AsyncResult(dict['celery_task_id']).state
        result.append(dict)
    return jsonify({'procs': result})


@api.route('/processes/<int:id>/')
def get_process_api(id):
    proc = ProcessDb.query.get_or_404(id)
    return jsonify(proc.to_json())

@api.route('/processes/progress/<int:id>/', methods=['GET'])
def get_process_progress(id):
    src_paths = ProcessDb.get_process_folders_folderPaths(id)
    dst_path = '/mnt/MZK' + ProcessDb.get_process_destination(id)
    current = 0
    total = 0
    for src_path in src_paths:
       current, total, current_space, total_space = DataMover.get_folder_progress(src_path=src_path + '/2', dst_path=dst_path)
    return jsonify({'src_paths': src_paths, 'dst_path': dst_path, 'current_files':current, 'total_files': total, 'current_space': current_space, 'total_space': total_space})


@api.route('/processes/celery_task/<id>', methods=['GET'])
def get_process_celery_task(id):
    result = AsyncResult(id)
    return {
            "ready": result.ready(),
            "state": result.state,
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
            "time": result.date_done
        }


@api.route('/processes/celery_task/remove/<id>', methods=['POST'])
def remove_celery_task(id):
    celery_app.control.revoke(id, terminate=True)
    return jsonify({"message": "Proces přenosu ukončen."})
    

@api.route('/processes/folders/<int:id>/')
def get_process_folders(id):
    proc = ProcessDb.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = proc.folders.paginate(page=page, per_page=25, error_out=False)
    folders = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.get_process_folders', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.get_process_folders', id=id, page=page+1)
    return jsonify({
        'folders': [folder.to_json() for folder in folders],
        'page': page,
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


# Checks whether file already exists at MZK
@api.route('/check_folder_conditions/home/<path:req_path>', methods=['GET'])
@api.route('/check_folder_conditions/<path:req_path>', methods=['GET'])
def check_if_folder_exists(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    return DataMover.check_conditions(abs_path, foldername, app.config['SMB_USER'], app.config['SMB_PASSWORD'])


@api.route('/folder/mzk/<folder_name>', methods=['GET'])
def is_folder_at_mzk(folder_name):
    result = DataMover.search_dst_folders(folder_name)
    return jsonify({'folder': folder_name, 'result': result})


@api.route('/folder/mzk/progress/', methods=['GET'])
def send_to_mzk_progress():
    src_path = request.args.get('src_path', default=None)
    dst_path = request.args.get('dst_path', default=None)
    if not src_path or not dst_path:
        return jsonify({'message': 'Error: src_path or dst_path is empty'})
    current, total, current_space, total_space = DataMover.get_folder_progress(src_path=src_path, dst_path=dst_path)
    return jsonify({'current_files':current, 'total_files': total, 'current_space': current_space, 'total_space': total_space}), 200

# Is it better to send path in json instead of baking the path into endpoint?
@api.route('/folder/mzk/send/home/<path:req_path>', methods=['POST'])
@api.route('/folder/mzk/send/<path:req_path>', methods=['POST'])
def api_send_to_mzk(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    try:
        dst_path = request.get_json()['dst_folder']
    except Exception as e:
        app.logger.error(e)
    r = api_create_process_and_run.delay(abs_path, dst_path, app.config['SMB_USER'], app.config['SMB_PASSWORD'])
    src_path = abs_path + '/2' #, "task_id" : r.task_id
    dst_path2 = '/mnt/MZK' + dst_path + '/' + foldername
    return jsonify({"Status" : "ok", "task_id" : r.task_id, "src_path": src_path, "dst_path": dst_path2}), 200


@api.route('/mzk/connection', methods=['GET'])
def get_mzk_connection():
    conn_exists, msg = DataMover.check_connection()
    mount_exists = DataMover.check_mount()
    return jsonify({"connection": conn_exists, "message": msg, "mount_exists": mount_exists})


@api.route('/mzk/dst-folders/', methods=['GET'])
def get_mzk_dst_folders():
    path = request.args.get("path")
    if path.endswith('..'):
        path = os.path.abspath(os.path.join(path, os.pardir))
    if path == '/':
        path = "/MUO"
    result = []
    i = 0
    for foldername in DataMover.get_mzk_folders(path):
        if foldername not in [u'.']:
            dict = {}
            dict['id'] = "folder" + str(i)
            dict['text'] = foldername
            dict['icon'] = 'jstree-folder'
            result.append(dict)
            i += 1
    response = {"current_folder": path ,"folders": result}
    return jsonify(response)

@shared_task(ignore_results=False, bind=True)
def api_create_process_and_run(self, src_path, dst_path, username, password):
    print(src_path, dst_path, username, password)
    mover = DataMover(src_path, dst_path, username, password, self.request.id)
    mover.move_to_mzk_now()