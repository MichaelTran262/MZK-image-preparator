from dataMover.ProcessWrapper import ProcessWrapper
from audioop import mul
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, render_template, url_for, abort, send_file, redirect, request, jsonify
import multiprocessing
import os
import time
import pyvips
import logging

DEBUG = True

if DEBUG:
    logger = logging.getLogger('werkzeug')
    BASE_DIR = '/home/mzk/Desktop/KromApp/image-preparator/testFolder'
else:
    logger = logging.getLogger('gunicorn.access')
    BASE_DIR = '/home/tran/test'

app = Flask(__name__)
fh = logging.FileHandler('./logs/preparator.log', 'a', 'utf-8')
logger.addHandler(fh)
dataSender = ProcessWrapper()
activeSenders = {}

@app.route('/', defaults={'req_path': ''})
@app.route('/home', defaults={'req_path': ''})
@app.route('/<path:req_path>')
@app.route('/home/<path:req_path>')
def index(req_path):
    abs_path = os.path.join(BASE_DIR, req_path)

    if not os.path.exists(abs_path):
        app.logger.error("BASE_DIR does not exist")
        return abort(404)

    files = os.listdir(abs_path)
    dirs = []
    for index, file in enumerate(files):
        tmp_path = os.path.join(abs_path, file)
        if os.path.isdir(tmp_path):
            tmp = {}
            tmp['dirname'] = file
            tmp['isdir'] = True
            tmp['hasDirTwo'] = False
            tmp['hasDirThree'] = False
            tmp['hasDirFour'] = False
            for dir in os.listdir(tmp_path):
                if dir == '2':
                    tmp['hasDirTwo'] = True
                elif dir == '3':
                    tmp['hasDirThree'] = True
                elif dir == '4':
                    tmp['hasDirFour'] = True
            dirs.append(tmp)
    #app.logger.info(dirs)            
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
        if len(multiprocessing.active_children()) > 2:
            files = os.listdir(BASE_DIR)  
            return render_template('modal.html', msg="Už běží dva jiné procesy. (Pokud chcete navýšit, napište správci)", files=files)
        for dir in dirs:
            if dir == 2:
                if not os.path.exists(dirs[dir]):
                    files = os.listdir(BASE_DIR)  
                    return render_template('modal.html', msg="Chybí složka 2", files=files)
            elif dir == 3 or dir == 4:
                if os.path.exists(dirs[dir]):
                    files = os.listdir(BASE_DIR)
                    return render_template('modal.html', msg="Složka 3 nebo 4 už existuje", files=files)
                else:
                    os.makedirs(dirs[dir])

        task_cp = multiprocessing.Process(target=copy_images, args=(dirs[2], dirs))
        task_cp.start()
        task_cp.join(1)
        
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
    dataSender.addFolder(request.args["folder"])
    return '', 200

@app.route('/remove_folder', methods=['POST'])
def remove_folder():
    dataSender.removeFolder(request.args["folder"])
    return '', 200

@app.route('/send_to_mzk', methods=['POST'])
def schedule_send():
    if request.args["time"]:
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
    chosenSender = activeSenders[request.args["globalId"]]
    chosenSender.killProcess()
    activeSenders.pop(request.args["globalId"])
    return '', 200

@app.route('/get_sender_processes', methods=['GET'])
def get_sender_processes():
    return jsonify([activeSender.getJson() for activeSender in activeSenders])

#End of endpoints

def check_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def convert_image(file, dirs, src_dir):
    ##app.logger.info(f'Preparing file {file}')
    filename = os.path.splitext(file)[0]
    # get absolute path
    file = os.path.join(src_dir, file)
    image = pyvips.Image.new_from_file(file)
    image3 = image.thumbnail_image(1920)
    image4 = image.thumbnail_image(800)
    image3_path = dirs[3] + '/' + filename
    image3.jpegsave(image3_path + ".jpeg")
    image4_path = dirs[4] + '/' + filename
    image4.jpegsave(image4_path + ".jpeg")

def copy_images(src_dir, dirs):
    tif_files = os.listdir(src_dir)
    start = time.perf_counter()
    pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()-2)
    pool.starmap(convert_image, [(file, dirs, src_dir) for file in tif_files if file.endswith('.tif') or file.endswith('.tiff')])
    pool.close()
    pool.join()
    finish = time.perf_counter()
    app.logger.info(f'Directory {src_dir} finished in {round(finish-start, 2)}')

if __name__ == "__main__":
    max_proc = multiprocessing.cpu_count()
    app.logger.info(" * MAX processes available: " + str(max_proc))
    app.run(debug=DEBUG)
