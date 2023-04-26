import os
import configparser
from dotenv import load_dotenv

PROJECT_DIR = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(PROJECT_DIR, '.env'))

class Config(object):
    MZK_IP = os.environ.get('MZK_IP', 'X.X.X.X:XXXX')
    TESTING = False
    DB_SERVER = 'mzk-postgres'
    
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_SERVER}/{self.DB_NAME}"
    
class ProductionConfig(Config):
    SRC_FOLDER = os.environ.get('SRC_FOLDER')
    DST_FOLDER = os.environ.get('DST_FOLDER') 
    DB_USER = 'postgres' #Production ready
    DB_PASSWORD = 'password' #Production ready
    DB_NAME = 'mzkdata' #Production ready
    SMB_USER = os.environ.get('SMB_USER') #Production ready
    SMB_PASSWORD = os.environ.get('SMB_PASSWORD') #Production ready

class DevelopmentConfig(Config):
    SRC_FOLDER = os.environ.get('SRC_FOLDER') or '/home/tran/Desktop/git/github/MichaelTran262/image-preparator/testFolder'
    DST_FOLDER = os.environ.get('DST_FOLDER') or '' # ADD MZK

    SMB_USER = os.environ.get('SMB_USER')
    SMB_PASSWORD = os.environ.get('SMB_PASSWORD')
    DB_USER = 'postgres'
    DB_PASSWORD = 'password'

class LocalDevelopmentConfig(DevelopmentConfig):
    DB_SERVER = 'localhost:5432'

