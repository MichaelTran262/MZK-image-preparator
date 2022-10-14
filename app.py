from audioop import mul
from email.policy import default
from flask import Flask, render_template, url_for, abort, send_file, redirect, request
import multiprocessing
import os
import pyvips

DEBUG = True

if DEBUG:
    BASE_DIR = '/Users/thanh/Desktop/git/github/MichaelTran262/image-preparator/test'
else:
    BASE_DIR = '/home/tran/test'

app = Flask(__name__)

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
    app.logger.info(files)
    for index, file in enumerate(files):
        tmp_path = os.path.join(abs_path, file)
        if os.path.isdir(tmp_path):
            tmp = {}
            tmp['dirname'] = file
            tmp['isdir'] = True
            tmp['hasDirTwo'] = False
            for dir in os.listdir(tmp_path):
                print(tmp_path)
                if dir == '2':
                    tmp['hasDirTwo'] = True
            dirs.append(tmp)
    #app.logger.info(dirs)            
    return render_template('index.html', files=dirs)

@app.route('/prepare/<path:req_path>', methods=['POST', 'GET'])
def prepare(req_path):
    print("HELLO");
    if request.method == 'POST':
        abs_path = os.path.join(BASE_DIR, req_path)
        print("Preparing " + abs_path)
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
        copy_images(dirs[2], dirs)
        
        #return redirect('/')
    else:
        return '', 204

def check_dir(path):
    print("Checking " + path)
    if not os.path.exists(path):
        os.makedirs(path)

def convert_image(file_path):
    print('Reading file')
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
    app.logger.info(tif_files)
    #pool = multiprocessing.Pool(processes=4)
    #pool.map(convert_image, [file for file in tif_files if file.endswith('.tif') or file.endswith('.tiff')])

if __name__ == "__main__":
    app.run(debug=DEBUG)
