from flask import jsonify, request, g, url_for, redirect, abort, render_template
from flask import current_app as app
from celery import shared_task
from celery import current_app as celery_app
from celery.result import AsyncResult
from ..models import ProcessDb
from ..dataMover.DataMover import DataMover
from ..dataMover.ProcessWrapper import ProcessWrapper
from . import api
import os

@api.route('/processes/')
def get_processes():
    procs = ProcessDb.query.paginate()


@api.route('/processes/<int:id>/')
def get_process_api(id):
    proc = ProcessDb.query.get_or_404(id)
    return jsonify(proc.to_json())


@api.route('/processes/celery_task/<id>', methods=['GET'])
def get_process_celery_task(id):
    result = AsyncResult(id)
    print(result.info)
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


@api.route('/send_to_mzk_now/progress/home/<path:req_path>', methods=['GET'])
@api.route('/send_to_mzk_now/progress/<path:req_path>', methods=['GET'])
def send_to_mzk_progress(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    foldername = os.path.split(abs_path)[1]
    current, total = DataMover.get_folder_progress(folder=abs_path, foldername=foldername, username=app.config['SMB_USER'], password=app.config['SMB_PASSWORD'])
    return jsonify({'current':current, 'total': total}), 200


@shared_task(ignore_results=False, bind=True)
def api_create_process_and_run(self, src_path, username, password):
    mover = DataMover(src_path, username, password, self.request.id)
    mover.move_to_mzk_now()