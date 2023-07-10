from flask import current_app, url_for
from datetime import datetime
from . import db
import enum
import json

folder_process = db.Table('folder_process',
                          db.Column("folder_id", db.Integer, db.ForeignKey('folder.id')),
                          db.Column("process_id", db.Integer, db.ForeignKey('process.id'))
                          )

class ProcessStatesEnum(enum.Enum):
    PENDING = 'PENDING'
    STARTED = 'STARTED'
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    REVOKED = 'REVOKED'

class ProcessDb(db.Model):

    __tablename__ = 'process'

    id = db.Column(db.Integer, primary_key=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    celery_task_id = db.Column(db.String, nullable=True)
    planned = db.Column(db.Boolean, nullable=False)
    status = db.Column(db.Enum(ProcessStatesEnum), nullable=False)
    start = db.Column(db.DateTime, default=None, nullable=True)
    stop = db.Column(db.DateTime, default=None, nullable=True)
    folders = db.relationship('FolderDb', secondary=folder_process, backref='processes')

    def __repr__(self):
        return f"Process(\
            id={self.id}, \
            created={self.created}, \
            planned={self.planned}, \
            start={self.start}, \
            stop={self.stop}, \
            status={str(self.status)}, \
            folders={self.folders})"
            

    def to_json(self):
        return {
            'id': self.id,
            'created': self.created,
            'celery_task_id': self.celery_task_id,
            'planned': self.planned,
            'status': str(self.status),
            'start': self.start,
            'stop': self.stop,
            'folders': url_for('api.get_process_folders', id=self.id)
        }
    
    def add_folder(self, folder):
        self.folders.append(folder)
        db.session.commit()
    
    @staticmethod
    def get_process(id):
        return ProcessDb.query.get(id)

    @staticmethod
    def get_folders(id):
        process = ProcessDb.query.get(id)
        return list(process.folders)
    
    @staticmethod
    def get_processes_by_page(page = 1):
        procs = ProcessDb.query.order_by(ProcessDb.created.desc()).paginate(page=page, per_page=10)
        return procs
    
    @staticmethod
    def get_process_folders(id):
        proc = ProcessDb.query.get(id)
        return proc.folders
    
    @staticmethod
    def get_planned_process():
        proc = ProcessDb.query.filter(ProcessDb.status == ProcessStatesEnum.PENDING and ProcessDb.planned==True).first()
        return proc
    
    @staticmethod 
    def set_process_to_started(id):
        proc = ProcessDb.query.get(id)
        proc.status = ProcessStatesEnum.STARTED
        db.session.commit()
    
    @staticmethod
    def set_process_to_failure(id):
        proc = ProcessDb.query.get(id)
        proc.status = ProcessStatesEnum.FAILURE
        db.session.commit()

    @staticmethod
    def set_process_to_success(id):
        proc = ProcessDb.query.get(id)
        proc.status = ProcessStatesEnum.SUCCESS
        db.session.commit()

    @staticmethod
    def set_celery_task_id(id, celery_id):
        proc = ProcessDb.query.get(id)
        proc.celery_task_id = celery_id
        db.session.commit()

class FolderDb(db.Model):
    
    __tablename__ = 'folder'

    id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String, nullable=False)
    folder_path = db.Column(db.String, nullable=False)
    dst_path = db.Column(db.String, nullable=True)
    # processes = db.relationship('ProcessDb', secondary=folder_process, backref='folders')
    start = db.Column(db.DateTime, default=None, nullable=True)
    end = db.Column(db.DateTime, default=None, nullable=True)
    images = db.relationship('Image', backref='folder')

    def __repr__(self):
        return f"Folder(                     \
            id={self.id!r},  \
            folder_name={self.folder_name!r},\
            folder_path={self.folder_path!r} \
            dst_path={self.dst_path}"


    @classmethod
    def create(cls, folder_name, folder_path):
        folder = cls(folder_name=folder_name, folder_path=folder_path)
        db.session.add(folder)
        db.session.commit()
        return folder


    @staticmethod
    def get_images(image_id):
        folder = FolderDb.query.get(image_id)
        return list(folder.images)


    @staticmethod
    def get_folder_path(id):
        folder = FolderDb.query.get(id)
        return folder.folder_path
    

    @staticmethod
    def set_start(id):
        folder = FolderDb.query.get(id)
        folder.start = datetime.utcnow()
        db.session.commit()
    

    @staticmethod
    def set_end(id):
        folder = FolderDb.query.get(id)
        folder.end = datetime.utcnow()
        db.session.commit()


class Image(db.Model):

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

    @staticmethod
    def get_images_by_page(page = 1):
        images = Image.query.order_by(Image.time_created.desc()).paginate(page=page, per_page=10)
        return images