from dataMover.ProcessWrapper import ProcessWrapper
from audioop import mul
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template, url_for, abort, send_file, redirect, request, jsonify
import multiprocessing
import os
import logging
from preparator.Preparator import Preparator
from dataMover.Utility import Utility
from dataMover.Database import ProcessDb, FolderDb

DEBUG = True

app = Flask(__name__)
util = Utility()
dataSender = ProcessWrapper(util)
activeSenders = {}

if DEBUG:
    logger = logging.getLogger('werkzeug')
    BASE_DIR = util.sourceFolder
else:
    logger = logging.getLogger('gunicorn.access')
    BASE_DIR = util.sourceFolder
fh = logging.FileHandler('/app/logs/preparator.log', 'a', 'utf-8')
logger.addHandler(fh)

# Endpointy začínají zde

@app.route('/', defaults={'req_path': ''})
@app.route('/home', defaults={'req_path': ''})
@app.route('/<path:req_path>')
@app.route('/home/<path:req_path>')
def index(req_path):
    abs_path = os.path.join(BASE_DIR, req_path)

    if not os.path.exists(abs_path):
        app.logger.error("BASE_DIR does not exist")
        return abort(404)

    dirs = Preparator.get_folders(abs_path)         
    return render_template('index.html', files=dirs)

@app.route('/prepare/<path:req_path>', methods=['POST', 'GET'])
def prepare(req_path):
    if request.method == 'POST':
        abs_path = os.path.join(BASE_DIR, req_path)
        dirs = {
            2: abs_path + '/2',
            3: abs_path + '/3',
            4: abs_path + '/4'
        }
        Preparator.prepare_folder(dirs, BASE_DIR, app)
        return '', 204
    else:
        return '', 204

@app.route('/active_proc_count', methods=['GET'])
def is_running():
    dict = {}
    dict['proc_count'] = len(multiprocessing.active_children())
    return jsonify(dict)

@app.route('/processes', methods=['GET'])
def get_processes():
    pass

#Chudyho endpointy

@app.route('/add_folder', methods=['POST'])
def add_new_folder():
    global dataSender
    dataSender.addFolder(request.args["folder"])
    return '', 200

@app.route('/remove_folder', methods=['POST'])
def remove_folder():
    global dataSender
    dataSender.removeFolder(request.args["folder"])
    return '', 200

@app.route('/send_to_mzk', methods=['POST'])
def schedule_send():
    global dataSender
    if "time" in request.args.keys():
        dataSender.setSendTime(request.args["time"])
    else:
        dataSender.setSendTime()
    dataSender.scheduleSend()
    globalId = dataSender.getGlobalId()
    activeSenders[globalId] = dataSender
    dataSender = ProcessWrapper()
    return '', 200
    
@app.route('/cancel_send', methods=['POST'])
def cancel_send():
    global activeSenders
    global dataSender
    chosenSender = activeSenders[request.args["globalId"]]
    chosenSender.killProcess()
    activeSenders.pop(request.args["globalId"])
    return '', 200

@app.route('/get_sender_processes', methods=['GET'])
def get_sender_processes():
    processes = ProcessDb.query()
    return render_template("processes.html", processes=processes);
    #return jsonify([activeSender.getJson() for activeSender in activeSenders])

#End of endpoints

def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == "__main__":
    max_proc = multiprocessing.cpu_count()
    app.logger.info(" * MAX processes available: " + str(max_proc))
    app.run(debug=DEBUG, host='0.0.0.0', port=80)
