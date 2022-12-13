from Utility import Utility
from ProcessWrapper import ProcsessStatus as pStat

class Folder():

    def __init__(self, path, utility):

        self.folderPath = path
        self.folderName = path.split("/")[-1]
        self.util = utility
        self.status = None
    
    def getFolderPath(self):
        return self.folderPath
    
    def getFolderName(self):
        return self.folderName
    
    def setFolderPathAndName(self, folderPath):
        self.folderPath = folderPath
        self.folderName = folderPath.split("/")[-1]
    
    """
    GETTERS AND SETTERS
    """
    def getStatus(self):
        return self.status
    
    def setStatus(self, status):
        self.status = status