from flask import Flask, render_template, abort, request, jsonify, redirect, url_for
from flask import current_app as app
from .. import socketIo
import multiprocessing
import threading
import os
import urllib.parse
from . import main
from ..preparator.Preparator import Preparator
from ..preparator.ImageWrapper import ImageWrapper
from ..dataMover.ProcessWrapper import ProcessWrapper
from ..dataMover.DataMover import DataMover
from ..models import ProcessDb, FolderDb
#from .. import db

#dataSender = ProcessWrapper(db)
# Endpointy začínají zde

@main.route('/', defaults={'req_path': ''})
@main.route('/home', defaults={'req_path': ''})
@main.route('/home/', defaults={'req_path': ''})
@main.route('/home/<path:req_path>')
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

    files = Preparator.get_folders(abs_path, req_path)
    file_count = Preparator.get_file_count(abs_path, req_path)
    return render_template('index.html', files=files, file_count=file_count, prev_page='/home'+prev_path)

@main.route('/prepare/<path:req_path>', methods=['POST', 'GET'])
def prepare(req_path):
    if request.method == 'POST':
        message = Preparator.prepare_folder(app.config['SRC_FOLDER'], app, req_path)
        abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
        files = Preparator.get_folders(abs_path, req_path)
        file_count = Preparator.get_file_count(abs_path, req_path)
        head, tail = os.path.split(req_path)
        return_path = urllib.parse.quote("/home/" + str(head))
        if message != '':
            return render_template('modal.html', 
                msg=message, 
                files=files, 
                file_count=file_count, 
                return_path=return_path)
        else:
            return render_template('modal_success.html', 
                msg="Konverze probíhá",
                files=files,
                file_count=file_count,
                return_path=return_path)
    elif request.method == 'GET':
        converted_file_count, total_files = Preparator.progress(req_path, app)
        return jsonify({'converted': converted_file_count, 'total_files': total_files})
    else:
        return '', 204

@main.route('/active_proc_count', methods=['GET'])
def is_running():
    dict = {}
    dict['proc_count'] = len(multiprocessing.active_children())
    return jsonify(dict)
    
@main.route('/processes', methods=['GET'])
def get_processes():
    page = request.args.get('page', 1, type=int)
    procs = ProcessWrapper.get_processes_by_page(page)
    if procs is None:
        abort(404)
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
    images = ImageWrapper.get_images_by_page(page)
    if images is None:
        abort(404)
    return render_template('images.html',images=images)

@main.route('/active-processes', methods=['GET'])
def get_active_processes():
    #global activeSenders
    #if activeSenders is None:
        #abort(404)
    #return jsonify([sender.getJson() for sender in activeSenders.values()])
    return '', 200

#Chudyho endpointy

@main.route('/add_folder/<path:req_path>', methods=['POST'])
@main.route('/add_folder/home/<path:req_path>', methods=['POST'])
def add_new_folder(req_path):
    if request.method == 'POST':
        abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
        dirs = {
            2: abs_path + '/2',
            3: abs_path + '/3',
            4: abs_path + '/4'
        }
        print(abs_path)
        return jsonify({"status": "ok"})
    else:
        return jsonify({"status": "ok"})

@main.route('/remove_folder', methods=['POST'])
def remove_folder():
    #global dataSender
    #dataSender.removeFolder(request.args["folder"])
    return jsonify({"status": "ok"})

@main.route('/send_to_mzk_now/home/<path:req_path>', methods=['POST'])
@main.route('/send_to_mzk_now/<path:req_path>', methods=['POST'])
def send_folder(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    t = threading.Thread(target=create_process_and_run, args=(abs_path, app.config['SMB_USER'], app.config['SMB_PASSWORD'], app._get_current_object()))
    t.daemon = True
    t.start()
    return redirect(url_for('main.get_processes'))

@main.route('/send_to_mzk_later/home/<path:req_path>', methods=['POST'])
@main.route('/send_to_mzk_later/<path:req_path>', methods=['POST'])
def schedule_send_folder(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    message = DataMover.move_to_mzk_later(abs_path)
    files = Preparator.get_folders(abs_path, req_path)
    file_count = Preparator.get_file_count(abs_path, req_path)
    head, tail = os.path.split(req_path)
    return_path = urllib.parse.quote("/home/" + str(head))
    if message != '':
        return render_template('modal.html', 
            msg=message, 
            files=files, 
            file_count=file_count, 
            return_path=return_path)
    else:
        return redirect(url_for('main.get_processes'))
    
    
@main.route('/cancel_send', methods=['POST'])
def cancel_send():
    return '', 200

#End of endpoints

def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def create_process_and_run(src_path, username, password, app):
    mover = DataMover(src_path, username, password)
    mover.move_to_mzk_now(app)

@socketIo.on('event')
def handle_event():
    print("SOCKET CONNECTED")