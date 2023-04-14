from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from . import db

class ProcessDb(db.Model):

    __tablename__ = 'process'

    processId = db.Column(db.Integer, primary_key=True)
    globalId = db.Column(db.String(40), nullable=False)
    folderId = db.Column(db.Integer, db.ForeignKey('folder.folderId'), nullable=False)
    pid = db.Column(db.Integer, nullable=True)
    scheduledFor = db.Column(db.DateTime, nullable=True)
    start = db.Column(db.DateTime, nullable=True)
    stop = db.Column(db.DateTime, nullable=True)
    forceful = db.Column(db.Boolean, nullable=True)
    processStatus = db.Column(db.Integer, nullable=False)

    __table_args__ = (db.UniqueConstraint('pid', 'stop', name='pid_stop_constaint'),)

    def __repr__(self):
        return f"Book(                          \
            globalId={self.globalId!r},         \
            pid={self.pid!r},                   \
            start={self.start!r},               \
            stop={self.stop!r}                  \
            scheduledFor={self.scheduledFor!r}  \
            processStatus={self.processStatus!r}\
            forcefull={self.forceful!r})"
    
    def serialize(self):
        return {
            'globalId' : self.globalId,
            'pid' : self.pid,
            'start' : self.start,
            'stop' : self.stop,
            'scheduledFor' : self.scheduledFor,
            'processStatus' : self.processStatus,
            'forcefull' : self.forceful
        }

class FolderDb(db.Model):
    
    __tablename__ = 'folder'

    folderId = db.Column(db.Integer, primary_key=True)
    folderName = db.Column(db.String, nullable=False)
    folderPath = db.Column(db.String, nullable=False)
    processes = db.relationship('ProcessDb', backref='folder')
    images = db.relationship('Image', backref='folder')

    def __repr__(self):
        return f"Book(                     \
            processId={self.processId!r},  \
            folderName={self.folderName!r},\
            folderPath={self.folderPath!r}"

class Image(db.Model):

    __tablename__ = 'image'

    imageId = db.Column(db.Integer, primary_key=True)
    folderId = db.Column(db.Integer, db.ForeignKey('folder.folderId'), nullable=False)
    filename = db.Column(db.String, nullable=False)
    time_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    #folder = db.relationship('FolderDb', backref='image')
