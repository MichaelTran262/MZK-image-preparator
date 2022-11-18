from Folder import Folder
from Utility import Utility
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

class Process():

    def __init__(self, folders, sendTime = datetime.now().isoformat()):
        
        self.folders = {}
        self.utility = Utility()
        for folder in folders:
            self.addFolder(folder)
        self.scheduler = BackgroundScheduler()
        self.scheduler.add_job()
        self.scheduler.

    def send(self):
        pass

    def killProcess(self):
        pass
    
    def addFolder(self, folder):
        self.folders[folder] = Folder(folder, self.utility)
    
    def removeFolder(self, folder):
        self.folders[folder] = None
    
    def getFolders(self):
        return self.folders