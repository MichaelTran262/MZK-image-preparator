from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Process(Base):

    __tablename__ = 'process'

    processId = Column(Integer, primary_key=True)
    pid = Column(Integer, nullable=False)
    start = Column(DateTime, nullable=False)
    stop = Column(DateTime, nullable=True)
    forceful = Column(Boolean, nullable=True)

    folder = relationship('Folder', backref='folder')
    __table_args__ = UniqueConstraint('pid', 'stop', name='pid_stop_constaint')

    def __repr__(self):
        return f"Book(                      \
            pid={self.pid!r},               \
            start={self.start!r}),          \
            stop={self.stop!r}              \
            forcefull={self.forceful!r})"
    
    def scp_and_remove(self):
        #sond folders with foreign key of process
        # hotovo

class Folder(Base):
    
    __tablename__ = 'folder'

    folderId = Column(Integer, primary_key=True)
    processId = Column(Integer, nullable=False, ForeignKey('Process.processId'))
    folderName = Column(String, nullable=False)
    folderPath = Column(String, nullable=False)

    def __repr__(self):
        return f"Book(                      \
            processId={self.processId!r},   \
            folderName={self.folderName!r}),\
            folderPath={self.folderPath!r}  \