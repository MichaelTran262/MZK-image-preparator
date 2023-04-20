from .. import db, socketIo
from flask_socketio import SocketIO
from ..models import FolderDb, ProcessDb
import os
import multiprocessing
import threading
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from smb.SMBConnection import SMBConnection

class ProcessMover():

    def __init__(self, src_path, user, password):
        self.dirs = dirs = {
            2: src_path + '/2',
            3: src_path + '/3',
            4: src_path + '/4'
        }
        self.src_path = src_path
        self.username = user
        self.password = password
    # sends only one path
    def move_to_mzk_now(self, app):
        for dir in self.dirs:
            if dir == 2:
                if not os.path.exists(self.dirs[dir]):
                    return "Chybí složka 2"
        self.send_files(app)
        return ""

    def move_to_mzk_later(self):
        for dir in self.dirs:
            if dir == 2:
                if not os.path.exists(self.dirs[dir]):
                    return "Chybí složka 2"
        return ""

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
                print("HELLO ", self.username)
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
            num_directories = 0
            num_files = 0
            for folder in process.folders:
                for path, subdirs, files in os.walk(folder.folderPath + '/2'):
                    num_directories += len(subdirs)
                    num_files += len(files)
            num_done_directories = 0
            num_done_files = 0
            for folder in process.folders:
                conn.createDirectory('NF', '/MUO/test_tran/' + folder.folderName)
                # send to MZK
                for path, subdirs, files in os.walk(folder.folderPath + '/2'):
                    for name in files:
                        file = os.path.join(path, name)
                        with open(file, 'rb') as local_f:
                            conn.storeFile('NF', '/MUO/test_tran/' + folder.folderName + '/' + name, local_f)
                        num_done_files += 1
                        socketIo.emit('progress', {'process_id': process.id, 'current': num_done_files, 'total': num_files})
            conn.close()
            # Change status to SENT
