import os
import pyvips
import multiprocessing
from flask import Flask, request, render_template, url_for, abort, send_file, redirect, request, jsonify
import time

class Preparator:

    @staticmethod
    def get_folders(path):
        files = os.listdir(path)
        dirs = []
        for index, file in enumerate(files):
            tmp_path = os.path.join(path, file)
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
        return dirs
    
    def prepare_folder(dirs, path, app):
        if len(multiprocessing.active_children()) > 2:
            files = os.listdir(path)  
            return render_template('modal.html', msg="Už běží dva jiné procesy. (Pokud chcete navýšit, napište správci)", files=files)
        for dir in dirs:
            if dir == 2:
                if not os.path.exists(dirs[dir]):
                    files = os.listdir(path)  
                    return render_template('modal.html', msg="Chybí složka 2", files=files)
            elif dir == 3 or dir == 4:
                if os.path.exists(dirs[dir]):
                    files = os.listdir(path)
                    return render_template('modal.html', msg="Složka 3 nebo 4 už existuje", files=files)
                else:
                    os.makedirs(dirs[dir])

        task_cp = multiprocessing.Process(target=Preparator.copy_images, args=(dirs[2], dirs, app))
        task_cp.start()
        task_cp.join(1)

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

    @staticmethod
    def copy_images(src_dir, dirs, app):
        tif_files = os.listdir(src_dir)
        start = time.perf_counter()
        pool = multiprocessing.Pool(processes=multiprocessing.cpu_count()-2)
        pool.starmap(Preparator.convert_image, [(file, dirs, src_dir) for file in tif_files if file.endswith('.tif') or file.endswith('.tiff')])
        pool.close()
        pool.join()
        finish = time.perf_counter()