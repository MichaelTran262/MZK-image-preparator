from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from dataMover import Database as md
from dataMover.Utility import Utility

def processes(count=100):
    fake = Faker()
    i = 0
    while i < count:
        p = md.ProcessDb(globalId=randint(1,10000),
                        pid=randint(1,10000),
                        scheduledFor=fake.future_date(),
                        start=fake.future_date(),
                        stop=fake.future_date(),
                        forceful=False,
                        processStatus=0)
        db = Utility()
        db.session.add(p)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()

def folders(count=100):
    fake = Faker()
    i = 0
    while i < count:
        f = md.FolderDb(folderName=fake.file_name(extension=".tif"),
                        folderPath=fake.file_path(depth=3))
        db = Utility()
        db.session.add(f)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()

