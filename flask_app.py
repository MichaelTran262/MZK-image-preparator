import os
import click
from app import create_app, db
from app.models import FolderDb, ProcessDb

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return dict(db=db, FolderDb=FolderDb, ProcessDb=ProcessDb)
