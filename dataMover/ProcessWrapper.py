import multiprocessing as mp
import os
from . import Database as db
import signal

from uuid import uuid4
from . import Folder
from . import Utility
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

class ProcsessStatus():
    SCHEDULED = 1
    IN_QUEUE = 2
    BEING_SENT = 3
    FINISHED = 4
    KILLED = 5

class ProcessWrapper():

    def __init__(self, util = Utility.Utility(), folders = [], sendTime = None):

        self.folders = {}
        self.utility = util
        self.globalId = uuid4()
        self.mpPid = None
        self.status = ProcsessStatus.SCHEDULED if sendTime else ProcsessStatus.IN_QUEUE
        for folder in folders:
            self.addFolder(folder)
        self.setStatus(self.status)
        self.scheduler = BackgroundScheduler()
        self.totalSize = self.__calculateTotalSize()

    def sendThroughRsync(self):
        if self.setStatus != ProcsessStatus.SCHEDULED and self.setStatus != ProcsessStatus.IN_QUEUE:
            self.utility.log("Process already sent, finished or killed")
            return
        self.setStatus(ProcsessStatus.BEING_SENT)
        self.utility.log("Creating process")
        process = mp.Process(target=self.sendThroughRsyncProcess)
        self.utility.log("Starting process")
        process.start()
        self.utility.log("Process started")
        process.join()
        self.utility.log("Process finished")
        self.setStatus(ProcsessStatus.FINISHED)
    
    def sendThroughRsyncProcess(self):
        self.utility.log("Sending files through Rsync")
        if self.__checkIfStringsAreValid([self.utility.port, self.utility.sshUser, self.utility.ipAddress]):
            raise Exception("Invalid ssh port, ssh user or ip address.")
        self.mpPid = os.getpid()
        session = self.utility.session
        session.query(db.ProcessDb)                         \
            .filter(db.ProcessDb.globalId == self.globalId) \
            .update({'pid': os.getpid()})
        for folder in self.folders:
            for root, dirs, files in os.walk(folder):
                for file in files:
                    fullpath = os.path.join(root, file)
                    if "&" in file:
                        raise Exception("Invalid file name")
                    self.utility.log("Sending file " + file)
                    # TODO
                    os.system("rsync -avz -e \"ssh -p {sshPort}\" {file} {sshUser}@{ipAddress}:{fileDest}".format(
                        sshPort=self.utility.port,
                        file=fullpath,
                        sshUser=self.utility.sshUser,
                        ipAddress=self.utility.ipAddress,
                        fileDest=os.path.split(fullpath)[0]
                    ))
                    self.utility.log("File " + file + " sent")
            self.utility.log("Files sent through Rsync")
    
    def __checkIfStringsAreValid(self, strings):
        for string in strings:
            if "&" in string:
                return False
        return True

    def killProcess(self):
        pid = self.mpPid
        if not pid:
            self.utility.log("Process not started")
            return
        self.setStatus(ProcsessStatus.KILLED)
        self.utility.log("Process " + str(pid) + " killed")
        os.kill(pid, signal.SIGTERM)
    
    def addFolder(self, folder):
        self.folders[folder] = Folder(folder, self.utility)
        self.folders[folder].setStatus(self.status)
        self.totalSize += self.folders[folder].getSize()
    
    def removeFolder(self, folder):
        self.totalSize -= self.folders[folder].getSize()
        self.folders[folder] = None
    
    def getFolders(self):
        return self.folders
    
    def setStatus(self, status):
        session = self.utility.session
        if status == ProcsessStatus.SCHEDULED:
            row = db.ProcessDb(
                globalId=self.globalId,
                pid=None,
                scheduledFor=None,
                start=None,
                stop=None,
                forceful=None,
                procsessStatus=status)
            session.add(row)
            session.commit()
            self.status = status
        elif status == ProcsessStatus.IN_QUEUE:
            self.status = status
        elif status == ProcsessStatus.BEING_SENT:
            session.query(db.ProcessDb)                         \
                .filter(db.ProcessDb.globalId == self.globalId) \
                .update({'start': datetime.now()})
            self.status = status
        elif status == ProcsessStatus.FINISHED:
            session.query(db.ProcessDb)                        \
                .filter(db.ProcessDb.globalId == self.globalId)\
                .update({'stop': datetime.now()})
            self.status = status
        self.status = status
        for folder in self.folders:
            self.folders[folder].setStatus(status)
    
    def setSendTime(self, sendTime = None):
        if sendTime:
            convertedTime = datetime.strptime(sendTime, "%Y-%m-%d %H:%M:%S")
        else:
            convertedTime = datetime.now()
        self.sendTime = convertedTime
        session = self.utility.session
        session.query(db.ProcessDb)                         \
            .filter(db.ProcessDb.globalId == self.globalId) \
            .update({'scheduledFor': convertedTime})
    
    def scheduleSend(self):
        if not self.sendTime:
            raise Exception("No send time specified")
        self.scheduler.add_job(self.sendThroughRsync, 'date', run_date=self.sendTime)
        self.scheduler.start()
        self.setStatus(ProcsessStatus.SCHEDULED)
    
    #Write a method which calculates the size of the folders and returns it
    def __calculateTotalSize(self):
        totalSize = 0
        for folder in self.folders:
            totalSize += self.folders[folder].getSize()
        return totalSize

    def getPid(self):
        return self.mpPid
    
    def getGlobalId(self):
        return self.globalId
    
    def getFolders(self):
        return self.folders
    
    def getStatus(self):
        return self.status
    
    def getJson(self):
        return {
            "globalId": self.globalId,
            "pid": self.mpPid,
            "status": self.status,
            "sendTime": self.sendTime,
            "totalSize": self.totalSize,
            "folders": [self.folders[folder].getJson() for folder in self.folders]
        }