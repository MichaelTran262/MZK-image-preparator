from . import Database as db
import logging
import configparser

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

class Utility():

    def __init__(self):
        self.logger = logging.getLogger("werkzeug")
        self.logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler("DataSender.log")
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)

        config = self.loadConfig()
        self.ipAddress = config["Destination"]["ip"].split(":")[0]
        self.port = config["Destination"]["ip"].split(":")[-1]
        self.destFolder = config["Destination"]["folder"]
        self.sshUser = config["Destination"]["user"]
        username = config["Database"]["username"]
        password = config["Database"]["password"]
        dbName = config["Database"]["dbName"]

        self.session = self.initDb(username, password, dbName)
    
    def initDb(self, username, password, dbName):
        URL = 'postgresql://{username}:{password}@localhost:8090/{dbName}' \
            .format(
                username=username,
                password=password,
                dbName=dbName
            )
        engine = create_engine(URL)
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
        
    def log(self, message):
        self.logger.info(message)
    
    def loadConfig(self):
        config = configparser.ConfigParser()
        config.read("senderConfig.txt")
        return config