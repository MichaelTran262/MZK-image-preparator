from .. import db, socketIo
from flask_socketio import SocketIO
from flask import current_app
from ..models import FolderDb, ProcessDb
import os
import multiprocessing
import threading
import time as t
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from smb.SMBConnection import SMBConnection


class DataMover():

    nf_path = '/MUO/test_tran/'

    def __init__(self, src_path, user, password, celery_task_id):
        self.dirs = dirs = {
            2: src_path + '/2',
            3: src_path + '/3',
            4: src_path + '/4'
        }
        self.src_path = src_path
        self.foldername = os.path.split(src_path)[1]
        self.username = user
        self.password = password
        self.total_files = 0
        self.total_directories = 0
        self.celery_task_id = celery_task_id

    # sends only one path
    def move_to_mzk_now(self):
        conds = DataMover.check_conditions(self.src_path, 
            self.foldername, self.username, self.password)
        if not conds['folder_two']:
            return
        if conds['exists_at_mzk']:
            return
        self.send_files()

    def move_to_mzk_later(self):
        for dir in self.dirs:
            if dir == 2:
                if not os.path.exists(self.dirs[dir]):
                    return "Chybí složka 2"
                
    @staticmethod
    def get_folder_progress(folder, foldername, username, password):
        mzk_path = os.path.join(DataMover.nf_path, foldername)
        return_dict = {}
        try:
            conn = SMBConnection(username, password, 'krom_app', '10.2.0.8', use_ntlm_v2=True)
        except Exception as e:
            print('SMBConnection object creation unsuccessfull: ' + e)
            return
        try:
            conn.connect('10.2.0.8', timeout=10)
            print('Connection successfull')
        except:
            print('Connection unsuccessfull: ' + e)
            return
        total_files = 0
        krom_dir2 = folder + '/2'
        for path, subdirs, files in os.walk(krom_dir2):
            total_files += len(files)
        transferred = []
        try:
            for path, subdirs, files in DataMover.smb_walk(conn, mzk_path):
                for name in files:
                    transferred.append(os.path.join(path, name))
        except Exception as e:
            return 0, 0
        return len(transferred), total_files

    @staticmethod
    def smb_walk(conn, path):
        dirnames = []
        filenames = []
        for file in conn.listPath('NF', path):
            if file.isDirectory:
                if file.filename not in [u'.', u'..']:
                    dirnames.append(file.filename)
            else:
                filenames.append(file.filename)
        yield path, dirnames, filenames
        for dirname in dirnames:
            for subpath in DataMover.smb_walk(conn, os.path.join(path, dirname)):
                yield subpath

    @staticmethod
    def check_conditions(src_path, foldername, username, password):
        mzk_path = DataMover.nf_path + foldername
        return_dict = {}
        krom_dir2_path = src_path + '/2'
        if not os.path.exists(krom_dir2_path):
            return_dict['folder_two'] = False
            return_dict['exists_at_mzk'] = False
            return return_dict
        else:
            return_dict['folder_two'] = True
        try:  
            conn = SMBConnection(username, password, 'krom_app', '10.2.0.8', use_ntlm_v2=True)
        except Exception as e:
            print('SMBConnection creation unsuccessfull: ', e)
            return return_dict
        try:
            conn.connect('10.2.0.8', timeout=10)
            print('Connection successfull')
        except Exception as e:
            print("Connection unsuccessfull")
            return return_dict
        # Create connection, listPath
        try:
            files = conn.listPath('NF', DataMover.nf_path)
        except Exception as e:
            print("Could not list files with listpath method")
            raise(e)
        return_dict['exists_at_mzk'] = False
        for file in files:
            if file.isDirectory:
                if foldername == file.filename:
                    return_dict['exists_at_mzk'] = True
        return return_dict

    def send_files(self):
        try:
            folder = FolderDb(folderName=os.path.split(self.src_path)[1], folderPath=self.src_path)
            db.session.add(folder)
            process = ProcessDb(celery_task_id=self.celery_task_id)
            process.folders.append(folder)
            db.session.add(process)
            db.session.commit()
        except Exception as e:
            print("Problem with dabatase: ", e)
            return
        conn = None
        try:  
            conn = SMBConnection(self.username, self.password, 'krom_app', '10.2.0.8', use_ntlm_v2=True)
        except Exception as e:
            print('SMBConnection creation unsuccessfull: ', e)
            return
        try:
            conn.connect('10.2.0.8')
            print('Connection successfull')
        except Exception as e:
            print("Connection unsuccessfull")
            return
        for folder in process.folders:
            for path, subdirs, files in os.walk(folder.folderPath + '/2'):
                self.total_directories += len(subdirs)
                self.total_files += len(files)
        done_directories = 0
        done_files = 0
        for folder in process.folders:
            conn.createDirectory('NF', '/MUO/test_tran/' + folder.folderName)
            # send to MZK
            # src dir is folder named 2
            src_dir = folder.folderPath + '/2'
            for path, subdirs, files in os.walk(src_dir):
                for dir in subdirs:
                    if dir not in [u'.', u'..']:
                        full_dir = os.path.join(path, dir)
                        rel_dir = os.path.relpath(full_dir, src_dir)
                        conn.createDirectory('NF', '/MUO/test_tran/' + folder.folderName + '/' + rel_dir)
                for filename in files:
                    file = os.path.join(path, filename)
                    rel_dir = os.path.relpath(path, src_dir)
                    rel_file = os.path.join(rel_dir, filename)
                    with open(file, 'rb') as local_f:
                        conn.storeFile('NF', '/MUO/test_tran/' + folder.folderName + '/' + rel_file, local_f)
                    t.sleep(1)
                    #done_files += 1
        conn.close()
        # Change status to SENT
