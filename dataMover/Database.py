from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import sessionmaker

Base = declarative_base()

class Process(Base):

    __tablename__ = 'process'

    processId = Column(Integer, primary_key=True)
    pid = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    stop = Column(DateTime, nullable=True)
    forcefull = Column(Boolean, nullable=True)

    folder = relationship('Folder', backref='folder')

class Folder(Base):
    
    __tablename__ = 'folder'

