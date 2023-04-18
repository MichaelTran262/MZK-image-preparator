from .. import db
from ..models import FolderDb, ProcessDb
import os
from datetime import datetime, time
from apscheduler.schedulers.background import BackgroundScheduler

class ProcessMover():

    @classmethod
    def move_to_mzk_now(cls, path):
        dirs = {
            2: path + '/2',
            3: path + '/3',
            4: path + '/4'
        }
        for dir in dirs:
            if dir == 2:
                if not os.path.exists(dirs[dir]):
                    return "Chybí složka 2"
        try:
            folder = FolderDb(folderName=path, folderPath=path)
            process = ProcessDb(processStatus='Created')
            process.folders.append(folder)
            db.session.add(folder)
            db.session.add(process)
            db.session.commit()
        except Exception as e:
            process = ProcessDb.create(path, path, "Error during process creation")
        return ""

    @classmethod
    def move_to_mzk_later(cls, path):
        dirs = {
            2: path + '/2',
            3: path + '/3',
            4: path + '/4'
        }
        for dir in dirs:
            if dir == 2:
                if not os.path.exists(dirs[dir]):
                    return "Chybí složka 2"
        try:
            folder = FolderDb(folderName=path, folderPath=path)
            now = datetime.now()
            midnight = time(0, 0)
            today_midnight = datetime.combine(now.date(), midnight)
            process = ProcessDb(processStatus='Created', scheduledFor=today_midnight)
            process.folders.append(folder)
            #spojeni 
            for folder in process.folders:
                # send to MZK
                pass

            db.session.add(folder)
            db.session.add(process)
            db.session.commit()
        except Exception as e:
            process = ProcessDb.create(path, path, "Error during process creation")
        return ""

    @classmethod
    def get_folders(cls, id):
        process = ProcessDb.query.get(id)
        return list(process.folders)


    @classmethod
    def get_sender_processes_by_page(page, process_id):
        pass
