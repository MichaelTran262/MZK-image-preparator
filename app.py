from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, url_for, abort, send_file, redirect, request, jsonify
import multiprocessing
import os
import time
import pyvips

DEBUG = True

if DEBUG:
    BASE_DIR = '/home/tran/Desktop/git/github/MichaelTran262/image-preparator/test'
else:
    BASE_DIR = '/home/tran/test'

app = Flask(__name__)

class InvalidUsage(Exception):
    status_code = 400

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv

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
        if task_cp.is_alive():
            print("Is alive")
        else:
            print("Is not alive")
        
        return '', 204
    else:
        return '', 204

@app.route('/active', methods=['GET', 'POST'])
def is_running():
    proc = False
    for running_proc in multiprocessing.active_children():
        print(running_proc.name)
        proc = True
    dict = {}
    if proc:
        dict['has_process'] = True
    else:
        dict['has_process'] = False
    return jsonify(dict)


@app.errorhandler(InvalidUsage)
def handle_invalid_usage(error):
    app.logger.info("Uhandel invalid usege")
    response = jsonify(error)
    response.status_code = error.status_code
    return response

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
    print(" * MAX processes available: " + str(max_proc))
    app.run(debug=DEBUG)
