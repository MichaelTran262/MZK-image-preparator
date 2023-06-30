from celery import shared_task
from celery.result import AsyncResult
import os
import grp
import pwd
from flask import Flask, request, render_template, url_for, abort, send_file, redirect, request, jsonify
from flask import current_app
from .. import models
import time as t
from datetime import datetime
from smb.SMBConnection import SMBConnection
from ..dataMover.DataMover import DataMover
from ..exceptions.prepare_exceptions import *

def check_condition(src_path):
    return_dict = {}
    krom_dirs = {
        2: src_path + '/2',
        3: src_path + '/3',
        4: src_path + '/4'
    }
    krom_dir2_path = src_path + '/2'
    # Folder two conditions
    if not os.path.exists(krom_dir2_path):
        return_dict['folder_two'] = False
        return_dict['folder_two_empty'] = True
        return_dict['folder_two_has_tiffs'] = False
    else:
        return_dict['folder_two'] = True
        if os.listdir(krom_dir2_path):
            return_dict['folder_two_empty'] = False
            return_dict['folder_two_has_tiffs'] = tiff_files_in_dir(krom_dir2_path)
        else:
            return_dict['folder_two_empty'] = True
            return_dict['folder_two_has_tiffs'] = False
    # Folder three conditions
    if os.path.exists(krom_dirs[3]):
        if os.listdir(krom_dirs[3]):   
            return_dict['folder_three_empty'] = False
        else:
            return_dict['folder_three_empty'] = True
    else:
        return_dict['folder_three_empty'] = True
    # Folder four conditions
    if os.path.exists(krom_dirs[4]):
        if os.listdir(krom_dirs[4]):   
            return_dict['folder_four_empty'] = False
        else:
            return_dict['folder_four_empty'] = True
    else:
        return_dict['folder_four_empty'] = True
    return return_dict


def tiff_files_in_dir(path):
    for path, subdirs, files in os.walk(path):
            for file in files:
                if file.lower().endswith(('.tiff', '.tif')):
                    return True
    return False

def get_folders(path, req_path):
    dirs = []
    with os.scandir(path) as files:
        for file in files:
            tmp_path = os.path.join(path, file)
            if not file.is_file():
                tmp = {}
                if req_path != '':
                    tmp['dirpath'] = req_path + "/" + file.name
                else:
                    tmp['dirpath'] = file.name
                tmp['dirname'] = file.name
                tmp['isdir'] = True
                tmp['hasDirTwo'] = False
                tmp['hasDirThree'] = False
                tmp['hasDirFour'] = False
                for dir in os.scandir(tmp_path):
                    if dir.name == '2':
                        tmp['hasDirTwo'] = True
                    elif dir.name == '3':
                        tmp['hasDirThree'] = True
                    elif dir.name == '4':
                        tmp['hasDirFour'] = True
                dir_info = os.stat(tmp_path)
                tmp['uid'] = dir_info.st_uid
                tmp['gid'] = dir_info.st_gid
                #is_folder_at_mzk(tmp['dirname'])
                #tmp['size'] = get_folder_size(tmp_path)
                dirs.append(tmp)
    return dirs

def get_file_count(path, req_path):
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

def get_folder_size(path):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size/1000000 # in megabytes


def prepare_folder(base_dir, app, req_path):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    uid, gid = 0, 0
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
            dir2_info = os.stat(dirs[dir])
            uid, gid = dir2_info.st_uid, dir2_info.st_gid
        elif dir == 3 or dir == 4:
            if os.path.exists(dirs[dir]):
                if os.listdir(dirs[dir]):   
                    return "Složka 3 nebo 4 už existuje a není prázdná"
            else:
                os.makedirs(dirs[dir])
                os.chown(dirs[dir], uid, gid)
                os.chmod(dirs[dir], 0o0777)
    copy_images(dirs[2], dirs, uid, gid)
    return ''


def copy_images(src_dir, krom_dirs, uid, gid):
    #tif_files = os.listdir(src_dir)
    folder = models.FolderDb.create(folder_name=src_dir, folder_path=src_dir)
    total_files = 0
    for root, dirs, files in os.walk(src_dir):
        total_files += len([file for file in files if file.endswith(".tiff") or file.endswith(".tif")])
    processed = 0
    for root, dirs, files in os.walk(src_dir):
        for dir in dirs:
            if dir not in [u'.', u'..']:
                full_path = os.path.join(root, dir)
                dir3 = os.path.join(krom_dirs[3], os.path.relpath(full_path, src_dir))
                os.makedirs(dir3)
                os.chown(dir3, uid, gid)
                os.chmod(dir3, 0o0777)
                dir4 = os.path.join(krom_dirs[4], os.path.relpath(full_path, src_dir))
                os.makedirs(dir4)
                os.chown(dir4, uid, gid)
                os.chmod(dir4, 0o0777)
        for filename in files:
            if filename.endswith(".tiff") or filename.endswith(".tif"):
                src_file = os.path.join(root, filename)
                rel_dir = os.path.relpath(root, src_dir)
                rel_file = os.path.join(rel_dir, filename)
                try:
                    convert_image.delay(rel_file, krom_dirs[3], krom_dirs[4], src_file, folder.id, uid, gid)
                except Exception as e:
                    print(e)
                    return


def progress(req_path, app):
    abs_path = os.path.join(app.config['SRC_FOLDER'], req_path)
    dirs = {
        "2": abs_path + '/2',
        "3": abs_path + '/3',
        "4": abs_path + '/4'
    }
    dir2 = os.path.join(abs_path, '2')
    dir3 = os.path.join(abs_path, '3')
    dir4 = os.path.join(abs_path, '4')
    total_files = 0
    for root, dirs, files in os.walk(dir2):
        total_files += len([file for file in files if file.endswith(".tiff") or file.endswith(".tif")])
    converted = 0
    for root, dirs, files in os.walk(dir3):
        converted += len([file for file in files if file.endswith(".jpg") or file.endswith(".jpeg")])
    return converted, total_files


@shared_task(ignore_results=False, bind=True)
def convert_image(self, rel_file, src_file, dst_dir3, dst_dir4, folder_id, uid, gid):
    '''
    Converts Image from tiff to Jpeg in given path
    :param rel_file: Relative file from folder 2 e.g. 0001.tif, it can be deeper with konvolut
    :param dir3: Folder 3 path e.g. {$DST_PATH}/DIG-XXX/3
    :param dir4: Folder 4 path e.g. {$DST_PATH}/DIG-XXX/3
    :param src_file: Source TIFF file to be converted. The file lies in folder 2.
    :param folder
    '''
    from pyvips import Image
    # get filename with extension
    try:
        image3 = Image.thumbnail(src_file, 1920)
        image4 = Image.thumbnail(src_file, 800)
    except SourceFileOpeningException as e:
        current_app.logger.error('Could not open and create image from source file ' + src_file)
        return
    try:
        # Gets last file (for konvolut)
        filename = os.path.basename(rel_file)
        # get only name of file without extension
        filename = os.path.splitext(rel_file)[0]
        jpeg_filename = filename + ".jpeg"
        # image3_path = dirs[3] + '/' + jpeg_filename
        image3_path = os.path.join(dst_dir3, jpeg_filename)
        image3.jpegsave(image3_path)
        # image4_path = dirs[4] + '/' + jpeg_filename
        image4_path = os.path.join(dst_dir4, jpeg_filename)
        image4.jpegsave(image4_path)
    except Exception as e:
        current_app.logger.error("Error in convert_image: Could not create jpeg file")
    try:
        os.chown(image3_path, uid, gid)
        os.chown(image4_path, uid, gid)
    except Exception as e:
        current_app.logger.error("Error in convert_image: Could not change file ownership")
    try:
        os.chmod(image3_path, 0o0777)
        os.chmod(image4_path, 0o0777)
    except Exception as e:
        current_app.logger.error("Error in convert_image: Could not change persmissions")
    try:
        models.Image.create(filename=jpeg_filename, folderId=folder_id, status="Ok", celery_task_id=self.request.id)
    except Exception as e:
        current_app.logger.error("Error in convert_image: Could not insert Image object to database")
        models.Image.create(filename=jpeg_filename, folderId=folder_id, status="error", celery_task_id=self.request.id)
        return