from flask import current_app, url_for
from datetime import datetime
from . import db

folder_process = db.Table('folder_process',
                          db.Column("folder_id", db.Integer, db.ForeignKey('folder.id')),
                          db.Column("process_id", db.Integer, db.ForeignKey('process.id'))
                          )

class ProcessDb(db.Model):

    #query: db.Query

    __tablename__ = 'process'

    id = db.Column(db.Integer, primary_key=True)
    #globalId = db.Column(db.String(40), nullable=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    celery_task_id = db.Column(db.String, nullable=False)
    scheduledFor = db.Column(db.DateTime, default=None, nullable=True)
    start = db.Column(db.DateTime, default=None, nullable=True)
    stop = db.Column(db.DateTime, default=None, nullable=True)
    #forceful = db.Column(db.Boolean, nullable=True)
    folders = db.relationship('FolderDb', secondary=folder_process, backref='processes')

    #__table_args__ = (db.UniqueConstraint('pid', 'stop', name='pid_stop_constaint'),)

    def __repr__(self):
        return f"Process(                          \
            start={self.start},               \
            stop={self.stop}                  \
            scheduledFor={self.scheduledFor}  \
            processStatus={self.processStatus!r}"

    def to_json(self):
        return {
            'id': self.id,
            'created': self.created,
            'scheduled_for': self.scheduledFor,
            'start' : self.start,
            'stop' : self.stop,
            'scheduledFor' : self.scheduledFor,
            'processStatus' : self.processStatus,
            'folders': url_for('api.get_process_folders', id=self.id)
        }

    @staticmethod
    def get_folders(id):
        process = ProcessDb.query.get(id)
        return list(process.folders)

    @staticmethod
    def get_sender_processes_by_page(page, process_id):
        pass

class FolderDb(db.Model):

    #query: db.Query
    
    __tablename__ = 'folder'

    id = db.Column(db.Integer, primary_key=True)
    folderName = db.Column(db.String, nullable=False)
    folderPath = db.Column(db.String, nullable=False)
    #processes = db.relationship('ProcessDb', secondary=folder_process, backref='folders')
    images = db.relationship('Image', backref='folder')

    def __repr__(self):
        return f"Folder(                     \
            id={self.id!r},  \
            folderName={self.folderName!r},\
            folderPath={self.folderPath!r}"
    
    @classmethod
    def create(cls, folderName, folderPath):
        folder = cls(folderName=folderName, folderPath=folderPath)
        db.session.add(folder)
        db.session.commit()
        return folder

    @staticmethod
    def get_images(id):
        folder = FolderDb.query.get(id)
        return list(folder.images)

class Image(db.Model):

    #query: db.Query

    __tablename__ = 'image'

    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=False)
    celery_task_id = db.Column(db.String, nullable=False)
    filename = db.Column(db.String, nullable=False)
    rel_path = db.Column(db.String, nullable=True)
    time_created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    status = db.Column(db.Text, nullable=False)
    #folder = db.relationship('FolderDb', backref='image')

    @classmethod
    def create(cls, filename, folderId, status, celery_task_id):
        image = cls(filename=filename, folder_id=folderId, status=status, celery_task_id=celery_task_id)
        db.session.add(image)
        db.session.commit()
        return image
