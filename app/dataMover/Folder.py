import os

class Folder():

    def __init__(self, path, utility):

        self.folderPath = path
        self.folderName = path.split("/")[-1]
        self.util = utility
        self.fileSize = self.__calculateSize()
        self.status = None
    
    def getFolderPath(self):
        return self.folderPath
    
    def getFolderName(self):
        return self.folderName
    
    def setFolderPathAndName(self, folderPath):
        self.folderPath = folderPath
        self.folderName = folderPath.split("/")[-1]
    
    def __calculateSize(self):
        totalSize = 0
        for root, dirs, files in os.walk(self.folderPath):
            for file in files:
                totalSize += os.path.getsize(os.path.join(root, file))
        return totalSize

    """
    GETTERS AND SETTERS
    """
    def getStatus(self):
        return self.status
    
    def setStatus(self, status):
        self.status = status
    
    def getSize(self):
        return self.fileSize
    
    def getJson(self):
        return {
            "folderPath": self.folderPath,
            "folderName": self.folderName,
            "fileSize": self.fileSize,
            "status": self.status
        }