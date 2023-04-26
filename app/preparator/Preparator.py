from .. import db, socketIo
import os
import pyvips
import multiprocessing
import threading
from flask import Flask, request, render_template, url_for, abort, send_file, redirect, request, jsonify
from .. import models
from .. import app
import time as t
from datetime import datetime
import urllib.parse

class Preparator:

    @classmethod
    def check_condition(cls, src_path):
        return_dict = {}
        krom_dirs = {
            2: src_path + '/2',
            3: src_path + '/3',
            4: src_path + '/4'
        }
        krom_dir2_path = src_path + '/2'
        if not os.path.exists(krom_dir2_path):
            return_dict['folder_two'] = False
        else:
            return_dict['folder_two'] = True
        if os.path.exists(krom_dirs[3]):
            if os.listdir(krom_dirs[3]):   
                return_dict['folder_three_empty'] = False
            else:
                return_dict['folder_three_empty'] = True
        else:
            return_dict['folder_three_empty'] = True
        if os.path.exists(krom_dirs[4]):
            if os.listdir(krom_dirs[4]):   
                return_dict['folder_four_empty'] = False
            else:
                return_dict['folder_four_empty'] = True
        else:
            return_dict['folder_four_empty'] = True
        return return_dict

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
                Pro přípravu obrázků v této složce klikněte na 'Připravit složky 3 a 4' v <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>1</b>", 
        elif str(abs_path).endswith('/2'):
            return "Nelze vytvořit obrázky ve složce s názvem <b>2</b>. \
                Pro přípravu obrázků v této složce klikněte na 'Připravit složky 3 a 4' v <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>2</b>"
        elif str(abs_path).endswith('/3'):
            return"Nelze vytvořit obrázky ve složce s názvem <b>3</b>. \
                Pro přípravu obrázků v této složce klikněte na 'Připravit složky 3 a 4' v <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>3</b>"
        elif str(abs_path).endswith('/4'):
            return "Nelze vytvořit obrázky ve složce s názvem <b>4</b>. \
                Pro přípravu obrázků v této složce klikněte na 'Připravit složky 3 a 4' ve <b>PŘEDCHOZÍ SLOŽCE</b> složky <b>4</b>"
        for dir in dirs:
            if dir == 2:
                if not os.path.exists(dirs[dir]):
                    return "Chybí složka 2"
            elif dir == 3 or dir == 4:
                if os.path.exists(dirs[dir]):
                    if os.listdir(dirs[dir]):   
                        return "Složka 3 nebo 4 už existuje a není prázdná"
                else:
                    os.makedirs(dirs[dir])
        cls.copy_images(dirs[2], dirs, app)
        t = threading.Thread(target=cls.copy_images, args=(dirs[2], dirs, app))
        t.daemon = True
        t.start()
        #task_cp = threading.Process(target=cls.copy_images, args=(dirs[2], dirs, app))
        #task_cp.start()
        #task_cp.join(1)
        return ''

    @classmethod
    def convert_image(cls, rel_file, dirs, src_file):
        ##app.logger.info(f'Preparing file {file}')
        #get filename with extension
        filename = os.path.basename(rel_file)
        try:
            #print("Converting: ", rel_file)
            image = pyvips.Image.new_from_file(src_file)
            image3 = image.thumbnail_image(1920)
            image4 = image.thumbnail_image(800)
            # get only name of file without extension
            filename = os.path.splitext(rel_file)[0]
            jpeg_filename = filename + ".jpeg"
            #image3_path = dirs[3] + '/' + jpeg_filename
            image3_path = os.path.join(dirs[3], jpeg_filename)
            image3.jpegsave(image3_path)
            #image4_path = dirs[4] + '/' + jpeg_filename
            image4_path = os.path.join(dirs[4], jpeg_filename)
            image4.jpegsave(image4_path)
            #models.Image.create(filename=jpeg_filename, folderId=folderId, status="ok")
        except Exception as e:
            print(e)
            #models.Image.create(filename=jpeg_filename, folderId=folderId, status=e)

    @classmethod
    def copy_images(cls, src_dir, krom_dirs, app):
        #tif_files = os.listdir(src_dir)
        start = t.perf_counter()
        #folder = models.FolderDb.create(folderName=src_dir, folderPath=src_dir)
        print("POOL SIZE: " + str(multiprocessing.cpu_count()))
        pool = multiprocessing.Pool(processes=8)
        socketIo.emit('preparation', "HELLO")
        total_files = 0
        for root, dirs, files in os.walk(src_dir):
            total_files += len([file for file in files if file.endswith(".tiff") or file.endswith(".tif")])
        processed = 0
        for root, dirs, files in os.walk(src_dir):
            for dir in dirs:
                full_path = os.path.join(root, dir)
                dir3 = os.path.join(krom_dirs[3], os.path.relpath(full_path, src_dir))
                os.makedirs(dir3)
                dir4 = os.path.join(krom_dirs[4], os.path.relpath(full_path, src_dir))
                os.makedirs(dir4)
            for filename in files:
                if filename.endswith(".tiff") or filename.endswith(".tif"):
                    src_file = os.path.join(root, filename)
                    rel_dir = os.path.relpath(root, src_dir)
                    rel_file = os.path.join(rel_dir, filename)
                    cls.convert_image(rel_file, krom_dirs, src_file)
                    #pool.apply_async(cls.convert_image, args=(rel_file, krom_dirs, src_dir, src_file))
                    processed += 1
                    print('current' + str(processed) + "\ntotal: " + str(total_files))
                    socketIo.emit('preparation', {'current': processed, 'total': total_files})
        #pool.starmap(Preparator.convert_image, 
            #[(file, dirs, src_dir, folder.folderId) for file in tif_files if file.endswith('.tif') or file.endswith('.tiff')])
        #pool.close()
        #pool.join()
        finish = t.perf_counter()

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