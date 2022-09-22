from flask import Flask, render_template, url_for, abort, send_file, redirect
import os
import pyvips

BASE_DIR = '/home/tran/Desktop/Kroměříž/App/test'

app = Flask(__name__)

@app.route('/')
@app.route('/home')
def index():
    abs_path = BASE_DIR

    if not os.path.exists(abs_path):
        return abort(404)

    files = os.listdir(abs_path)  

    return render_template('index.html', files=files)

@app.route('/prepare/<path:req_path>')
def prepare(req_path):
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
                return render_template('modal.html', msg=f"Složka 3 nebo 4 už existuje", files=files)
            else:
                os.makedirs(dirs[dir])        
    copy_images(dirs[2], dirs)
    return redirect('/')

def check_dir(path):
    print("Checking " + path)
    if not os.path.exists(path):
        os.makedirs(path)

def copy_images(src_dir, dirs):
    for file in os.listdir(src_dir):
        print(file)
        if file.endswith('.tiff') or file.endswith('.tif'):
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
        else:
            continue

if __name__ == "__main__":
    app.run(debug=True)
