from flask import Flask, render_template, abort, request, jsonify
from flask import current_app as app
import multiprocessing
import os
import urllib.parse
from . import main
from ..preparator.Preparator import Preparator
from ..dataMover.ProcessWrapper import ProcessWrapper
#from .. import db

#dataSender = ProcessWrapper(db)
# Endpointy začínají zde

@main.route('/', defaults={'req_path': ''})
@main.route('/home', defaults={'req_path': ''})
@main.route('/<path:req_path>')
@main.route('/home/<path:req_path>')
def index(req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)

    if not os.path.exists(abs_path):
        app.logger.error("BASE_DIR does not exist")
        return abort(404)

    if req_path != '':
        prev_path, tail = os.path.split(req_path)
        if prev_path == '':
            prev_path = ''
        else:
            prev_path = '/' + prev_path
    else:
        prev_path = ''

    dirs = Preparator.get_folders(abs_path, req_path)
    file_count = Preparator.get_file_count(abs_path, req_path)
    return render_template('index.html', files=dirs, file_count=file_count, prev_page='/home'+prev_path)

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
    print(page)
    procs = ProcessWrapper.get_processes_by_page(page)
    if procs is None:
        abort(404)
    return render_template('processes.html', processes=procs)

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

@main.route('/send_to_mzk', methods=['POST'])
def schedule_send():
    #global dataSender
    #if "time" in request.args.keys():
    #    dataSender.setSendTime(request.args["time"])
    #else:
    #    dataSender.setSendTime()
    #dataSender.scheduleSend()
    #globalId = dataSender.getGlobalId()
    #activeSenders[globalId] = dataSender
    #dataSender = ProcessWrapper()
    return '', 200
    
@main.route('/cancel_send', methods=['POST'])
def cancel_send():
    #global activeSenders
    #global dataSender
    #chosenSender = activeSenders[request.args["globalId"]]
    #chosenSender.killProcess()
    #activeSenders.pop(request.args["globalId"])
    return '', 200

#@main.route('/get_sender_processes', methods=['GET'])
#def get_sender_processes():
    #ProcessWrapper.get_processes_by_page(1);
#    return jsonify([sender.getJson() for sender in activeSenders.values()])

#End of endpoints

def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
