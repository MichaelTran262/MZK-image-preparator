import os
import pyvips
import multiprocessing
from flask import Flask, request, render_template, url_for, abort, send_file, redirect, request, jsonify
from .. import models
from .. import db
from .. import app
import time
from datetime import datetime
import urllib.parse

class Preparator:

    @classmethod
    def get_folders(cls, path, req_path):
        files = os.listdir(path)
        dirs = []
        for index, file in enumerate(files):
            tmp_path = os.path.join(path, file)
            if os.path.isdir(tmp_path):
                tmp = {}
                if req_path != '':
                    tmp['dirpath'] = req_path + "/" + file
                else:
                    tmp['dirpath'] = file
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
    
    @classmethod
    def get_file_count(cls, path, req_path):
        content = os.listdir(path)
        files = []
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.tif', '.tiff', '.ico')
        for index, file in enumerate(content):
            tmp_path = os.path.join(path, file)
            if os.path.isfile(tmp_path):
                if file.endswith(image_extensions):
                    tmp = {}
                    if req_path != '':
                        tmp['dirpath'] = req_path + "/" + file
                    else:
                        tmp['dirpath'] = file
                    tmp['filename'] = file
                    tmp['isdir'] = False
                    files.append(tmp)
        return len(files)
    
    @classmethod
    def prepare_folder(cls, base_dir, app, req_path):
        abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
        dirs = {
            2: abs_path + '/2',
            3: abs_path + '/3',
            4: abs_path + '/4'
        }
        if str(abs_path).endswith('/1'):
            return "Nelze vytvořit obrázky ve složce s názvem <b>1</b>. \
                Pro přípravu obrázků v této složce klikněte na 'Připravit' v <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>1</b>", 
        elif str(abs_path).endswith('/2'):
            return "Nelze vytvořit obrázky ve složce s názvem <b>2</b>. \
                Pro přípravu obrázků v této složceu klikněte na 'Připravit' v <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>2</b>"
        elif str(abs_path).endswith('/3'):
            return"Nelze vytvořit obrázky ve složce s názvem <b>3</b>. \
                Pro přípravu obrázků v této složce klikněte na 'Připravit' v <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>3</b>"
        elif str(abs_path).endswith('/4'):
            return "Nelze vytvořit obrázky ve složce s názvem <b>4</b>. \
                Pro přípravu obrázků v této složce klikněte na 'Připravit' ve <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>4</b>"

        if len(multiprocessing.active_children()) > 2:
            files = os.listdir(base_dir)  
            return "Už běží dva jiné procesy!"
        for dir in dirs:
            if dir == 2:
                if not os.path.exists(dirs[dir]):
                    return "Chybí složka 2"
            elif dir == 3 or dir == 4:
                if os.path.exists(dirs[dir]):
                    files = os.listdir(base_dir)
                    return "Složka 3 nebo 4 už existuje"
                else:
                    os.makedirs(dirs[dir])
        task_cp = multiprocessing.Process(target=cls.copy_images, args=(dirs[2], dirs, app))
        task_cp.start()
        task_cp.join(1)
        return ''

    @classmethod
    def convert_image(cls, file, dirs, src_dir, folderId):
        ##app.logger.info(f'Preparing file {file}')
        #get filename with extension
        filename = os.path.basename(file)
        try:
            image = pyvips.Image.new_from_file(file)
            image3 = image.thumbnail_image(1920)
            image4 = image.thumbnail_image(800)
            #print("HELLO")
            # get only name of file without extension
            filename = os.path.splitext(filename)[0]
            jpeg_filename = filename + ".jpeg"
            image3_path = dirs[3] + '/' + jpeg_filename
            image3.jpegsave(image3_path)
            image4_path = dirs[4] + '/' + jpeg_filename
            image4.jpegsave(image4_path)
            models.Image.create(filename=jpeg_filename, folderId=folderId, status="ok")
        except Exception as e:
            print(e)
            models.Image.create(filename=jpeg_filename, folderId=folderId, status=e)

    @classmethod
    def copy_images(cls, src_dir, krom_dirs, app):
        #tif_files = os.listdir(src_dir)
        start = time.perf_counter()
        folder = models.FolderDb.create(folderName=src_dir, folderPath=src_dir)
        print("POOL SIZE: " + str(multiprocessing.cpu_count()))
        pool = multiprocessing.Pool(4)
        for root, dirs, files in os.walk(src_dir):
            for filename in files:
                if filename.endswith(".tiff") or filename.endwith(".tif"):
                    tiff_file = os.path.join(src_dir, filename)
                    pool.apply_async(cls.convert_image, args=(tiff_file, krom_dirs, src_dir, folder.folderId))
        #pool.starmap(Preparator.convert_image, 
            #[(file, dirs, src_dir, folder.folderId) for file in tif_files if file.endswith('.tif') or file.endswith('.tiff')])
        pool.close()
        pool.join()
        finish = time.perf_counter()

    @classmethod
    def progress(cls, req_path, app):
        abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
        dirs = {
            2: abs_path + '/2',
            3: abs_path + '/3',
            4: abs_path + '/4'
        }
        total = len(os.listdir(dirs[2]))
        converted = len(os.listdir(dirs[4]))
        return converted, total