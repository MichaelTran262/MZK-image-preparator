from . import Database as db
import logging
import configparser

from os.path import exists
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
        socket = config["destination"]["ip"]
        if socket.find(":") == -1:
            self.ipAddress = socket
            self.port = "22"
        else:
            self.ipAddress, self.port = socket.split(":")
        self.destFolder = config["destination"]["folder"]
        self.sshUser = config["destination"]["user"]
        self.sourceFolder = config["source"]["folder"]
        username = config["database"]["username"]
        password = config["database"]["password"]
        dbName = config["database"]["dbName"]
        if "port" not in config["database"]:
            postgresPort = "5432"

        self.session = self.initDb(username, password, dbName, postgresPort)
    
    def initDb(self, username, password, dbName, postgresPort):
        URL = 'postgresql://{username}:{password}@db:{port}/{dbName}' \
            .format(
                username=username,
                password=password,
                dbName=dbName,
                port=postgresPort
            )
        engine = create_engine(URL)
        db.Base.metadata.create_all(engine)
        Session = sessionmaker(bind=engine)
        return Session()
        
    def log(self, message):
        self.logger.info(message)
    
    def loadConfig(self):
        config = configparser.ConfigParser()
        if not exists("dataMover/senderConfig.txt"):
            raise Exception("No config file found")
        config.read("dataMover/senderConfig.txt")
        return config