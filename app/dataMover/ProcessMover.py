from .. import db, socketIo
from flask import current_app
from flask_socketio import SocketIO
from ..models import FolderDb, ProcessDb
import os
import multiprocessing
import threading
import time as t
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from smb.SMBConnection import SMBConnection

class ProcessMover():

    nf_path = '/MUO/test_tran/'

    def __init__(self, src_path, user, password):
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

    # sends only one path
    def move_to_mzk_now(self, app):
        conds = ProcessMover.check_conditions(self.src_path, 
            self.foldername, self.username, self.password)
        if not conds['folder_two']:
            return
        if conds['exists_at_mzk']:
            return
        self.send_files(app)

    def move_to_mzk_later(self):
        for dir in self.dirs:
            if dir == 2:
                if not os.path.exists(self.dirs[dir]):
                    return "Chybí složka 2"

    @staticmethod
    def check_conditions(src_path, foldername, username, password):
        mzk_path = ProcessMover.nf_path + foldername
        return_dict = {}
        krom_dir2_path = src_path + '/2'
        if not os.path.exists(krom_dir2_path):
            return_dict['folder_two'] = False
        else:
            return_dict['folder_two'] = True
        try:  
            conn = SMBConnection(username, password, 'krom_app', '10.2.0.8', use_ntlm_v2=True)
        except Exception as e:
            print('SMBConnection creation unsuccessfull: ', e)
            return return_dict
        try:
            conn.connect('10.2.0.8')
            print('Connection successfull')
        except Exception as e:
            print("Connection unsuccessfull")
            return return_dict
        # Create connection, listPath
        files = conn.listPath('NF', ProcessMover.nf_path)
        return_dict['exists_at_mzk'] = False
        for file in files:
            if file.isDirectory:
                if foldername == file.filename:
                    return_dict['exists_at_mzk'] = True
        return return_dict

    def send_files(self, app):
        with app.app_context():
            try:
                folder = FolderDb(folderName=os.path.split(self.src_path)[1], folderPath=self.src_path)
                db.session.add(folder)
                process = ProcessDb(processStatus='Created')
                process.folders.append(folder)
                db.session.add(process)
                db.session.commit()
                print("Insertion OK")
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
                for path, subdirs, files in os.walk(folder.folderPath + '/2'):
                    for name in files:
                        file = os.path.join(path, name)
                        with open(file, 'rb') as local_f:
                            conn.storeFile('NF', '/MUO/test_tran/' + folder.folderName + '/' + name, local_f)
                        done_files += 1
                        socketIo.emit('progress', {'process_id': process.id, 'current': done_files, 'total': self.total_files})
            conn.close()
            # Change status to SENT