from flask import Flask, render_template, abort, request, jsonify, redirect, url_for
from flask import current_app as app
from celery.result import AsyncResult
import multiprocessing
import threading
import os
import urllib.parse
from . import main
from ..preparator.Preparator import get_folders, get_file_count, prepare_folder, progress, get_folder_size
from ..dataMover.DataMover import DataMover
from ..models import ProcessDb, FolderDb, Image
#from .. import db


@main.route('/', defaults={'req_path': ''}, methods=['GET'])
@main.route('/<path:req_path>:', defaults={'req_path': ''}, methods=['GET'])
@main.route('/home/', defaults={'req_path': ''}, methods=['GET'])
@main.route('/home/<path:req_path>', methods=['GET'])
def index(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)

    if not os.path.exists(abs_path):
        app.logger.error("abs path: " + abs_path + " does not exist")
        return abort(404)

    if req_path != '':
        prev_path, tail = os.path.split(req_path)
        if prev_path == '':
            prev_path = ''
        else:
            prev_path = '/' + prev_path
    else:
        prev_path = ''

    files = get_folders(abs_path, req_path)
    file_count = get_file_count(abs_path, req_path)
    return render_template('index.html', files=files, file_count=file_count, prev_page='/home'+prev_path)


@main.route('/processes', methods=['GET'])
def get_processes():
    page = request.args.get('page', 1, type=int)
    procs = ProcessDb.get_processes_by_page(page)
    if procs is None:
        abort(404)
    for proc in procs:
        proc.state = AsyncResult(proc.celery_task_id).state
    return render_template('processes.html', processes=procs)


@main.route('/get_process_folders/<int:id>', methods=['GET'])
def get_process_folders(id):
    proc = ProcessDb.query.get(id)
    folders = ProcessDb.get_folders(id)
    return render_template("process_folders.html", process=proc.id, folders=folders)


@main.route('/folder_images/<int:id>', methods=['GET'])
def get_folder_images(id):
    folder = FolderDb.query.get(id)
    images = FolderDb.get_images(id)
    return render_template("folder_images.html", folder=folder.folderName, images=images)


@main.route('/images', methods=['GET'])
def get_images():
    page = request.args.get('page', 1, type=int)
    images = Image.get_images_by_page(page)
    if images is None:
        abort(404)
    return render_template('images.html',images=images)


@main.route('/celery_task/<id>', methods=['GET'])
def get_process_celery_task(id):
    result = AsyncResult(id)
    dict = {
            "uuid": id,
            "ready": result.ready(),
            "state": result.state,
            "successful": result.successful(),
            "value": result.result if result.ready() else None,
            "time": result.date_done,
            "traceback": result.traceback if result.traceback else "Žádný"
        }
    return render_template('celery_task.html', record=dict)
#End of endpoints

def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_process_and_run(src_path, username, password, app):
    mover = DataMover(src_path, username, password)
    mover.move_to_mzk_now(app)
