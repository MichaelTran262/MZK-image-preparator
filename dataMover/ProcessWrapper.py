import multiprocessing as mp
import os
import Database as db

from Folder import Folder
from Utility import Utility
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler

class ProcsessStatus():
    SCHEDULED = 1
    IN_QUEUE = 2
    BEING_SENT = 3
    FINISHED = 4
    KILLED = 5

class ProcessWrapper():

    def __init__(self, folders, sendTime = None):

        self.folders = {}
        self.utility = Utility()
        self.status = ProcsessStatus.SCHEDULED if sendTime else ProcsessStatus.IN_QUEUE
        for folder in folders:
            self.addFolder(folder)
            self.folders[folder].setStatus(self.status)
        self.scheduler = BackgroundScheduler()
        self.sendTime = sendTime if sendTime else datetime.now()
        self.scheduler.add_job(self.send, 'date', run_date=self.sendTime)
        self.scheduler.start()

    def send(self):
        for folder in self.folders:
            if "&" not in folder:
                self.sendThroughGridFTP(self, folder)
            else:
                raise Exception("Invalid folder name")

    def sendThroughRsync(self, folder):
        self.status = ProcsessStatus.BEING_SENT
        self.folders[folder].setStatus(self.status)
        self.utility.log("Sending folder " + folder + " through Rsync")
        self.utility.log("Creating process")
        process = mp.Process(target=self.sendThroughRsyncProcess, args=(folder,))
        self.utility.log("Starting process")
        process.start()
        self.utility.log("Process started")
        process.join()
        self.utility.log("Process finished")
        self.status = ProcsessStatus.FINISHED
        self.folders[folder].setStatus(self.status)
        self.utility.log("Folder " + folder + " sent through Rsync")
    
    #Method to go through the folder and send the files with Rsync
    def sendThroughRsyncProcess(self, folder):
        self.utility.log("Sending files through Rsync")
        if self.checkIfStringsAreValid([self.utility.port, self.utility.sshUser, self.utility.ipAddress]):
            raise Exception("Invalid ssh port, ssh user or ip address.")
        for root, dirs, files in os.walk(folder):
            for file in files:
                if "&" in file:
                    raise Exception("Invalid file name")
                self.utility.log("Sending file " + file)
                os.system("rsync -avz -e \"ssh -p {sshPort}\" {file} {sshUser}@{ipAddress}:{file}".format(
                    sshPort=self.utility.port,
                    file=file,
                    sshUser=self.utility.sshUser,
                    ipAddress=self.utility.ipAddress
                ))
                self.utility.log("File " + file + " sent")
        self.utility.log("Files sent through Rsync")
    
    def checkIfStringsAreValid(self, strings):
        for string in strings:
            if "&" in string:
                return False
        return True

    def killProcess(self):
        pass
    
    def addFolder(self, folder):
        self.folders[folder] = Folder(folder, self.utility)
    
    def removeFolder(self, folder):
        self.folders[folder] = None
    
    def getFolders(self):
        return self.folders
    
    def setStatus(self, status):
        session = self.utility.session
        if status == ProcsessStatus.SCHEDULED:
            row = db.ProcessDb(
                pid=os.getpid(),
                jobCreated=self.sendTime,
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
            session.query(db.ProcessDb)                 \
                .filter(db.ProcessDb.pid == os.getpid())\
                .update({'start': datetime.now()})
            self.status = status
        elif status == ProcsessStatus.FINISHED:
            session.query(db.ProcessDb)                 \
                .filter(db.ProcessDb.pid == os.getpid())\
                .update({'stop': datetime.now()})
            self.status = status
        self.status = status
        
        for folder in self.folders:
            self.folders[folder].setStatus(status)