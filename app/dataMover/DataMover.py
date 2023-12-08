from .. import db
from flask import current_app
from ..models import FolderDb, ProcessDb, ProcessStatesEnum
from ..exceptions.exceptions import TransferException
from smb.SMBConnection import SMBConnection
from pyvips import Image
import os
import re
import shutil
import time as t


class DataMover():


    def __init__(self, src_path=None, dst_path=None, username=None, password=None, celery_task_id=None):
        self.src_path = src_path
        self.dst_path = dst_path
        self.username = username
        self.password = password
        self.total_files = 0
        self.total_directories = 0
        self.celery_task_id = celery_task_id


    def create_process(self, foldername, planned):
        abs_path = self.src_path
        dst_path = self.dst_path
        proc = ProcessDb.get_planned_process()
        if planned:
            if proc:
                folder = FolderDb(folder_name=foldername, folder_path=abs_path, dst_path=dst_path)
                ProcessDb.add_folder(proc, folder)
                current_app.logger.debug("Planned Process already exists")
                return proc
            else:
                current_app.logger.debug("Planned process does not exist")
                try:
                    folder = FolderDb(folder_name=foldername, folder_path=abs_path, dst_path=dst_path)
                    db.session.add(folder)
                    process = ProcessDb(planned=planned, status=ProcessStatesEnum.PENDING)
                    process.folders.append(folder)
                    db.session.add(process)
                    db.session.commit()
                except Exception as e:
                    current_app.logger.error("Problem with database: ", e)
                    raise TransferException("Problem with database: ", e)
                return process
        else:
            try:
                folder = FolderDb(folder_name=foldername, folder_path=abs_path, dst_path=dst_path)
                db.session.add(folder)
                process = ProcessDb(planned=planned, status=ProcessStatesEnum.PENDING)
                process.folders.append(folder)
                db.session.add(process)
                db.session.commit()
            except Exception as e:
                current_app.logger.error("Problem with database: ", e)
                raise TransferException("Problem with database: ", e)
            return process


    def move_to_mzk_now(self, process):
        for folder in process.folders:
            try:
                FolderDb.set_size(folder.id)
            except:
                ProcessDb.set_process_to_failure(process.id)
                raise TransferException(e)
            try:
                FolderDb.set_start(folder.id)
            except Exception as e:
                ProcessDb.set_process_to_failure(process.id)
                raise TransferException(e)
            conds = DataMover.check_conditions(folder.folder_path, folder.folder_name)
            if not conds['folder_two']:
                ProcessDb.set_process_to_failure(process.id)
                raise TransferException(folder.folder_name + " does not have folder 2")
            if conds['exists_at_mzk']:
                ProcessDb.set_process_to_failure(process.id)
                raise TransferException(folder.folder_name + " exists in MZK")
            try:
                self.send_files_os(folder)
                FolderDb.set_end(folder.id)
            except Exception as e:
                ProcessDb.set_process_to_failure(process.id)
                raise TransferException(e)
        ProcessDb.set_process_to_success(process.id)
                
            
    def send_files_os(self, folder):
        files_to_ignore = ['Thumbs.db', '.BridgeSort']
        dst_path = '/mnt/MZK' + folder.dst_path + '/' + folder.folder_name
        if os.path.exists(dst_path):
            current_app.logger.error("DEST PATH ALREADY EXISTS")
            raise TransferException(dst_path + " already exists!")
        #current_app.logger.debug("DEST_PATH: " + dst_path) # je zatim bez predpony /mnt/MZK
        os.makedirs(dst_path, exist_ok=True)
        # send to MZK
        # src dir is folder named 2
        src_dir = folder.folder_path + '/2'
        #current_app.logger.debug("src_dir: " + src_dir)
        if os.path.exists(src_dir):

            for path, subdirs, files in os.walk(src_dir):
                # filter out undesired files
                files = [f for f in files if (
                            f not in files_to_ignore and 
                            (f.endswith(".tiff") or f.endswith(".tif"))
                         )
                        ]
                # Create directories (for convolutes)
                for dir in subdirs:
                    if dir not in [u'.', u'..']:
                        full_dir = os.path.join(path, dir)
                        rel_dir = os.path.relpath(full_dir, src_dir)
                        dst_dir = dst_path + '/' + rel_dir
                        current_app.logger.debug("Creating directory: " + 
                                                dst_dir)
                        os.makedirs(dst_dir, exist_ok=True)
                        
                for filename in files:
                    file = os.path.join(path, filename)
                    rel_dir = os.path.relpath(path, src_dir)
                    rel_file = os.path.join(rel_dir, filename)
                    dst_file = os.path.join(dst_path, rel_file)
                    dst_file = os.path.normpath(dst_file)
                    current_app.logger.debug("Transferring FROM: " + file)
                    current_app.logger.debug("Transferring TO: " + dst_file)
                    if DataMover.is_high_dpi(file):
                        DataMover.send_pyvips(file, dst_file)
                    else:
                        shutil.copy2(file, dst_file)


    @staticmethod
    def is_high_dpi(src_file):
        image = Image.new_from_file(src_file)
        current_ppm_x = image.xres
        current_ppi_x = round(current_ppm_x * 25.4)
        if current_ppi_x == 600:
            return True
        return False

    @staticmethod
    def send_pyvips(src_file, dst_file):
        #TODO send do destination using Image.tiffsave
        target_ppi = 300
        image = Image.new_from_file(src_file)
        current_ppm_x = image.xres
        current_ppi_x = current_ppm_x * 25.4 # 600 expected always
        scaling_factor = round(target_ppi / current_ppi_x, 1) # 0.5 expected always
        new_image = image.resize(scaling_factor)
        res = target_ppi / 25.4
        new_image.tiffsave(dst_file, xres=res, yres=res, resunit="inch")

    @staticmethod
    def get_active_count(celery_app):
        active_tasks = celery_app.control.inspect().active()
        active_task_length = sum(len(tasks) for tasks in active_tasks.values()) if active_tasks else 0
        return active_task_length


    @staticmethod
    def check_connection():
        username = str(current_app.config['SMB_USER'])
        password = str(current_app.config['SMB_PASSWORD'])
        ip = str(current_app.config['MZK_IP'])
        #if os.path.exists('/mnt/MZK/MUO'):
        #    return True, "MZK is mounted"
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
    def check_mount():
        return os.path.ismount('/mnt/MZK/MUO') and len(os.listdir('/mnt/MZK/MUO')) != 0


    @staticmethod
    def establish_connection():
        """
        Creates an SMBConnection instance and creates a connection to MZK.
        :returns conn: SMBConnection with active MZK connection.
        """
        username = str(current_app.config['SMB_USER'])
        password = str(current_app.config['SMB_PASSWORD'])
        #current_app.logger.debug("SMB_USERNAME: " + username + ", SMB_PASSWORD: ***" + password[-2:])
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
    def get_folder_progress(dst_path):
        """
        Gets progress of a given folder. Counts total files in source directory and then counts files
        already existing in destination directory
        :param folder: folder e.g. ????
        :param foldername: foldername e.g. ????
        """
        dst_path = '/mnt/MZK' + dst_path
        transferred = 0
        try:
            for path, subdirs, files in os.walk(dst_path):
                transferred += len(files)
        except Exception as e:
            return 0, 0
        transferred_space = DataMover.get_folder_size(dst_path)
        return transferred, transferred_space
    

    @staticmethod
    def get_folder_size(path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size/1000000 # in megabytes


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
        '''
        Lists 
        '''
        # Working with mount
        if not DataMover.check_mount():
            current_app.logger.error("MZK disk not available!")
            return
        found = DataMover.find_directory_os('/mnt/MZK/MUO', folder_name)
        return found
        

    @staticmethod
    def find_directory_os(path, folder_name):
        for path, subdirs, files in os.walk(path):
            for dir in subdirs:
                if folder_name.lower() == dir.lower():
                    print(f"{path}/{folder_name}")
                    return f"{path}/{folder_name}"
            subdirs[:] = [d for d in subdirs if not re.match('^dig', d, re.I) and not re.match('^kdig', d, re.I) and d.lower() != folder_name.lower()]
        return None
    

    @staticmethod
    def check_conditions(src_path, foldername):
        return_dict = {}
        krom_dir2_path = src_path + '/2'
        if DataMover.check_connection():
            return_dict['mzk_connection'] = True
        else:
            return_dict['mzk_connection'] = False
        if DataMover.check_mount():
            return_dict['mzk_mount'] = True
        else:
            return_dict['mzk_mount'] = False
        if not os.path.exists(krom_dir2_path):
            return_dict['folder_two'] = False
            return_dict['exists_at_mzk'] = False
            return return_dict
        else:
            return_dict['folder_two'] = True
        folder_result = DataMover.search_dst_folders(foldername)
        if folder_result:
            return_dict['exists_at_mzk'] = True
            return_dict['mzk_path'] = os.path.relpath(folder_result, '/mnt/MZK')
        else:
            return_dict['exists_at_mzk'] = False
        return return_dict
    

    @staticmethod
    def get_mzk_folders(path):
        directories = ['..']
        abs_path = '/mnt/MZK' + path
        files = os.listdir(abs_path)
        for file in files:
            if os.path.isdir(os.path.join(abs_path, file)):
                if not re.match('^dig', file, re.I) and not re.match('^kdig', file, re.I):
                    directories.append(file)
        return directories
    
    
    @staticmethod
    def get_mzk_folders_pysmb(path):
        directories = []
        conn = DataMover.establish_connection()
        files = conn.listPath('NF', path)
        for file in files:
            if file.isDirectory:
                if not re.match('^dig', file.filename, re.I) and not re.match('^kdig', file.filename, re.I):
                    directories.append(file.filename)
        return directories