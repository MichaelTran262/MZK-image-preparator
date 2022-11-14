from Folder import Folder
from Utility import Utility
from datetime import datetime

class Process():

    def __init__(self, folders, sendTime = datetime.now().isoformat()):
        
        self.folders = {}
        self.utility = Utility()
        for folder in folders:
            self.folders[folder] = Folder(folder, self.utility)
        self.sendTime = sendTime