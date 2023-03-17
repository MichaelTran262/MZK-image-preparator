from flask import Flask, render_template, abort, request, jsonify, current_app
import multiprocessing
import os
from . import main
from ..preparator.Preparator import Preparator
#from ..dataMover.ProcessWrapper import ProcessWrapper
from ..Utility import Utility
#from .. import db

#dataSender = ProcessWrapper(db)
BASE_DIR = '/mnt/testFolder'
# Endpointy začínají zde

@main.route('/', defaults={'req_path': ''})
@main.route('/home', defaults={'req_path': ''})
@main.route('/<path:req_path>')
@main.route('/home/<path:req_path>')
def index(req_path):
    abs_path = os.path.join(BASE_DIR, req_path)

    if not os.path.exists(abs_path):
        current_app.logger.error("BASE_DIR does not exist")
        return abort(404)

    dirs = Preparator.get_folders(abs_path)         
    return render_template('index.html', files=dirs)

@main.route('/prepare/<path:req_path>', methods=['POST', 'GET'])
def prepare(req_path):
    if request.method == 'POST':
        abs_path = os.path.join(BASE_DIR, req_path)
        dirs = {
            2: abs_path + '/2',
            3: abs_path + '/3',
            4: abs_path + '/4'
        }
        Preparator.prepare_folder(dirs, BASE_DIR, current_app)
        return '', 204
    else:
        return '', 204

@main.route('/active_proc_count', methods=['GET'])
def is_running():
    dict = {}
    dict['proc_count'] = len(multiprocessing.active_children())
    return jsonify(dict)
    
#End of endpoints

def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)
