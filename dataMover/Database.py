from sqlalchemy import Column, String, Integer, Boolean, DateTime, ForeignKey, UniqueConstraint, relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from ProcessWrapper import ProcsessStatus

Base = declarative_base()

class ProcessDb(Base):

    __tablename__ = 'process'

    processId = Column(Integer, primary_key=True)
    pid = Column(Integer, nullable=False)
    jobCreated = Column(DateTime, nullable=False)
    start = Column(DateTime, nullable=True)
    stop = Column(DateTime, nullable=True)
    forceful = Column(Boolean, nullable=True)
    processStatus = Column(Integer, nullable=False)

    folder = relationship('Folder', backref='folder')
    __table_args__ = UniqueConstraint('pid', 'stop', name='pid_stop_constaint')

    def __repr__(self):
        return f"Book(                      \
            pid={self.pid!r},               \
            start={self.start!r}),          \
            stop={self.stop!r}              \
            jobCreated={self.jobCreated!r}  \
            processStatus={self.processStatus!r} \
            forcefull={self.forceful!r})"

class FolderDb(Base):
    
    __tablename__ = 'folder'

    folderId = Column(Integer, primary_key=True)
    processId = Column(Integer, ForeignKey('Process.processId'), nullable=False)
    folderName = Column(String, nullable=False)
    folderPath = Column(String, nullable=False)

    def __repr__(self):
        return f"Book(                      \
            processId={self.processId!r},   \
            folderName={self.folderName!r}),\
            folderPath={self.folderPath!r}"