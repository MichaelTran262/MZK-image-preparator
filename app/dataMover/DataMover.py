from .. import db
from flask import current_app
from ..models import FolderDb, ProcessDb
import os
import multiprocessing
import threading
import time as t
import shutil
import re
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler
from smb.SMBConnection import SMBConnection


class DataMover():

    # Na konci musí být lomitko!!!
    nf_paths = ['/MUO/TIF/', '/MUO/BEZ OCR/', '/MUO/OCR/', '/MUO/K OREZU/', '/MUO/test_tran/']

    def __init__(self, src_path, dst_path, user, password, celery_task_id):
        self.dirs = dirs = {
            2: src_path + '/2',
            3: src_path + '/3',
            4: src_path + '/4'
        }
        self.src_path = src_path
        self.dst_path = dst_path
        self.foldername = os.path.split(src_path)[1]
        self.username = user
        self.password = password
        self.total_files = 0
        self.total_directories = 0
        self.celery_task_id = celery_task_id


    # sends only one path
    def move_to_mzk_now(self):
        # TODO rewrite it
        conds = DataMover.check_conditions(self.src_path, 
            self.foldername, self.username, self.password)
        if not conds['folder_two']:
            return
        if conds['exists_at_mzk']:
            return
        self.send_files()

    # TODO
    def move_to_mzk_later(self):
        for dir in self.dirs:
            if dir == 2:
                if not os.path.exists(self.dirs[dir]):
                    return "Chybí složka 2"


    @staticmethod
    def check_connection():
        username = str(current_app.config['SMB_USER'])
        password = str(current_app.config['SMB_PASSWORD'])
        ip = str(current_app.config['MZK_IP'])
        if os.path.exists('/mnt/MZK/MUO'):
            return True, "MZK is mounted"
        try:
            conn = SMBConnection(username, password, 'krom_app', ip, use_ntlm_v2=True)
        except Exception as e:
            current_app.logger.error('SMBConnection object creation unsuccessfull')
            raise(e)
        try:
            auth = conn.connect(ip, timeout=5)
        except Exception as e:
            return False, "Problem with host, check MZK connection"
        if auth:
            return True, "Connection OK"
        else:
            return False, "Authentication unsuccessfull!"

    @staticmethod
    def establish_connection():
        """
        Creates an SMBConnection instance and creates a connection to MZK.
        :returns conn: SMBConnection with active MZK connection.
        """
        username = str(current_app.config['SMB_USER'])
        password = str(current_app.config['SMB_PASSWORD'])
        ip = str(current_app.config['MZK_IP'])
        try:
            conn = SMBConnection(username, password, 'krom_app', ip, use_ntlm_v2=True)
        except Exception as e:
            current_app.logger.error('SMBConnection object creation unsuccessfull')
            raise(e)
        try:
            conn.connect(ip, timeout=10)
            current_app.logger.debug('Connection successfull')
        except Exception as e:
            current_app.logger.debug('Connection UNSUCCESSFULL')
            raise(e)
        return conn


    @staticmethod
    def get_folder_progress(folder, foldername):
        """
        Gets progress of a given folder. Counts total files in source directory and then counts files
        already existing in destination directory
        :param folder: folder e.g. ????
        :param foldername: foldername e.g. ????
        """
        dst_folder = DataMover.search_dst_folders(folder_name=foldername)
        mzk_path = os.path.join(dst_folder, foldername)
        return_dict = {}
        #conn = DataMover.establish_connection()
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
        """
        walks through smb directory in given path
        :param conn: SmbConnection instance connected to SMB share
        :param path: path which will be walked through e.g. /home/user/dir
        """
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
    def search_dst_folders(folder_name):
        conn = DataMover.establish_connection()
        for path in DataMover.nf_paths:
            found = DataMover.find_directory(conn, path, folder_name)
            if found is not None:
                return found
        return None


    @staticmethod
    def find_directory(conn, path, folder_name):
        dirs = conn.listPath('NF', path)
        for dir in dirs:
            if dir.filename not in [u'.', u'..']:
                #print(dir.filename)
                if dir.isDirectory and dir.filename == folder_name:
                    return f"{path}/{folder_name}"
                elif dir.isDirectory:
                    sub_dir_path = f"{path}/{dir.filename}"
                    found_dir = DataMover.find_directory(conn, sub_dir_path, folder_name)
                    if found_dir is not None:
                        return found_dir
        return None
    

    @staticmethod
    def check_conditions(src_path, foldername, username, password):
        return_dict = {}
        krom_dir2_path = src_path + '/2'
        if not os.path.exists(krom_dir2_path):
            return_dict['folder_two'] = False
            return_dict['exists_at_mzk'] = False
            return return_dict
        else:
            return_dict['folder_two'] = True
        folder_result = DataMover.search_dst_folders(foldername)
        if folder_result:
            return_dict['exists_at_mzk'] = True
        else:
            return_dict['exists_at_mzk'] = False
        return return_dict
    
    
    @staticmethod
    def get_dst_folders():
        return DataMover.nf_paths
    
    
    @staticmethod
    def get_mzk_folders(path):
        directories = []
        conn = DataMover.establish_connection()
        files = conn.listPath('NF', path)
        for file in files:
            if file.isDirectory:
                if not re.match('^dig', file.filename, re.I) and not re.match('^kdig', file.filename, re.I):
                    directories.append(file.filename)
        return directories

    def send_files(self):
        try:
            folder = FolderDb(folderName=os.path.split(self.src_path)[1], folderPath=self.src_path)
            db.session.add(folder)
            process = ProcessDb(celery_task_id=self.celery_task_id)
            process.folders.append(folder)
            db.session.add(process)
            db.session.commit()
        except Exception as e:
            current_app.logger.error("Problem with dabatase: ", e)
            return
        conn = DataMover.establish_connection()
        for folder in process.folders:
            for path, subdirs, files in os.walk(folder.folderPath + '/2'):
                self.total_directories += len(subdirs)
                self.total_files += len(files)
        for folder in process.folders:
            dest_path = self.dst_path + '/' + folder.folderName
            if os.path.exists(dest_path):
                return
            os.makedirs(dest_path)
            # send to MZK
            # src dir is folder named 2
            src_dir = folder.folderPath + '/2'
            for path, subdirs, files in os.walk(src_dir):
                for dir in subdirs:
                    if dir not in [u'.', u'..']:
                        full_dir = os.path.join(path, dir)
                        rel_dir = os.path.relpath(full_dir, src_dir)
                        current_app.logger.debug("Creating directory: " + 
                                                 self.dst_path + '/' + 
                                                 folder.folderName + '/' + 
                                                 rel_file)
                        conn.createDirectory('NF', self.dst_path + '/' + 
                                             folder.folderName + '/' + 
                                             rel_dir)
                for filename in files:
                    file = os.path.join(path, filename)
                    rel_dir = os.path.relpath(path, src_dir)
                    rel_file = os.path.join(rel_dir, filename)
                    
                    storeFile = False
                    if storeFile:
                        with open(file, 'rb') as local_f:
                           conn.storeFile('NF', self.dst_path + '/' + 
                                          folder.folderName + '/' + 
                                          rel_file, local_f, show_progress=True)
                    else:
                        try:
                            dest_path = "/mnt/MZK/" + self.dst_path
                            dest_path = os.path.join(dest_path, folder.folderName, rel_file)
                            current_app.logger.debug("BEFORE normpath: " + dest_path)
                            dest_path = os.path.normpath(dest_path)
                            current_app.logger.debug("Transferring FROM: " + file)
                            current_app.logger.debug("Transferring TO: " + dest_path)
                            shutil.copy2(file, dest_path)
                        except Exception as e:
                            current_app.logger.error(e)
                    #done_files += 1
        conn.close()
        # Change status to SENT
