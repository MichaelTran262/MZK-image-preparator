from flask import current_app, url_for
from datetime import datetime
from . import db

folder_process = db.Table('folder_process',
                          db.Column("folder_id", db.Integer, db.ForeignKey('folder.id')),
                          db.Column("process_id", db.Integer, db.ForeignKey('process.id'))
                          )


class ProcessDb(db.Model):

    __tablename__ = 'process'

    id = db.Column(db.Integer, primary_key=True)
    # globalId = db.Column(db.String(40), nullable=True)
    created = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    celery_task_id = db.Column(db.String, nullable=False)
    scheduledFor = db.Column(db.DateTime, default=None, nullable=True)
    start = db.Column(db.DateTime, default=None, nullable=True)
    stop = db.Column(db.DateTime, default=None, nullable=True)
    # forceful = db.Column(db.Boolean, nullable=True)
    folders = db.relationship('FolderDb', secondary=folder_process, backref='processes')
    destination = db.Column(db.String, nullable=False)

    # __table_args__ = (db.UniqueConstraint('pid', 'stop', name='pid_stop_constaint'),)

    def __repr__(self):
        return f"Process(                          \
            start={self.start},               \
            stop={self.stop}                  \
            scheduledFor={self.scheduledFor}  \
            processStatus={self.processStatus!r}"

    def to_json(self):
        return {
            'id': self.id,
            'celery_task_id': self.celery_task_id,
            'created': self.created,
            'scheduled_for': self.scheduledFor,
            'start': self.start,
            'stop': self.stop,
            'scheduledFor': self.scheduledFor,
            'folders': url_for('api.get_process_folders', id=self.id)
        }
    
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
    def get_process_destination(id):
        proc = ProcessDb.query.get(id)
        return proc.destination
    
    @staticmethod
    def get_process_folders_folderpaths(id):
        proc = ProcessDb.query.get(id)
        paths = []
        for folder in proc.folders:
            paths.append(folder.folder_path)
        return paths

class FolderDb(db.Model):
    
    __tablename__ = 'folder'

    id = db.Column(db.Integer, primary_key=True)
    folder_name = db.Column(db.String, nullable=False)
    folder_path = db.Column(db.String, nullable=False)
    dest_path = db.Column(db.String, nullable=True)
    # processes = db.relationship('ProcessDb', secondary=folder_process, backref='folders')
    images = db.relationship('Image', backref='folder')

    def __repr__(self):
        return f"Folder(                     \
            id={self.id!r},  \
            folder_name={self.folder_name!r},\
            folder_path={self.folder_path!r} \
            dest_path={self.dest_path}"


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