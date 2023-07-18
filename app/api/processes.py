from flask import jsonify, request, url_for, abort
from celery import current_app as celery_app
from celery.result import AsyncResult
from ..models import ProcessDb, FolderDb
from ..dataMover.DataMover import DataMover
from . import api
import os


@api.route('/processes', methods=['GET'])
def get_processes_api():
    '''
    Returns processes by page where every process has:
        id, created, celery_task_id, planned (Boolean), start, stop, status and folders 
    '''
    page = request.args.get('page', 1, type=int)
    procs = ProcessDb.get_processes_by_page(page)
    result = []
    if procs is None:
        abort(404)
    for proc in procs:
        dict = proc.to_json()
        if dict['celery_task_id']:
            dict['state'] = AsyncResult(dict['celery_task_id']).state
        result.append(dict)
    return jsonify({'procs': result})


@api.route('/processes/<int:id>/')
def get_process_api(id):
    '''
    Returns specific process by id
    '''
    proc = ProcessDb.query.get_or_404(id)
    return jsonify(proc.to_json())


@api.route('/processes/progress/<int:id>/', methods=['GET'])
def get_process_progress(id):
    '''
    Returns progress of a process
    '''
    folders = ProcessDb.process_folders(id)
    current = 0
    total = 0
    current_space = 0
    total_space = 0
    for folder in folders:
       dst_path = os.path.join(folder.dst_path, folder.folder_name)
       current_fold, current_space_f = DataMover.get_folder_progress(dst_path=dst_path)
       current += current_fold
       total += folder.filecount
       current_space += current_space_f
       total_space += folder.size
    return jsonify({'current_files':current, 
                    'total_files': total, 
                    'current_space': current_space, 
                    'total_space': total_space})


@api.route('/processes/celery_task/<id>', methods=['GET'])
def get_process_celery_task(id):
    '''
    Returns a celery task which is tied to a ProcessDb object
    '''
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
    '''
    Removes celery running celery task
    '''
    celery_app.control.revoke(id, terminate=True)
    proc = request.get_json()
    if not proc:
        return jsonify({"message": "/celery_task/remove chybí proces objekt."})
    id = proc['id']
    ProcessDb.set_process_to_revoked(id)
    return jsonify({"message": "Proces přenosu ukončen. Již přenesené soubory nebyly smazány."})


@api.route('/processes/celery/active', methods=['GET'])
def get_active_tasks():
    '''
    Returns count of active celery tasks
    '''
    count = DataMover.get_active_count(celery_app)
    return jsonify({'active': count})


@api.route('/processes/folders/<int:id>/')
def process_folders(id):
    '''
    Returns folders of a proces of id
    '''
    proc = ProcessDb.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    pagination = proc.folders.paginate(page=page, per_page=25, error_out=False)
    folders = pagination.items
    prev = None
    if pagination.has_prev:
        prev = url_for('api.process_folders', id=id, page=page-1)
    next = None
    if pagination.has_next:
        next = url_for('api.process_folders', id=id, page=page+1)
    return jsonify({
        'folders': [folder.to_json() for folder in folders],
        'page': page,
        'prev': prev,
        'next': next,
        'count': pagination.total
    })


@api.route('/process_folders/<int:proc_id>/remove/<int:folder_id>', methods=['POST'])
def remove_process_folder(proc_id, folder_id):
    proc = ProcessDb.query.get(proc_id)
    folder = FolderDb.query.get(folder_id)
    folders = ProcessDb.get_folders(proc_id)
    ProcessDb.remove_folder(proc_id, folder)
    return jsonify({"message": "Ok"})