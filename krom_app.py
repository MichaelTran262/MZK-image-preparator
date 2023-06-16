import click
import os
from app import create_app


flask_app = create_app(os.getenv('FLASK_CONFIG') or 'development') # development, production
celery_app = flask_app.extensions["celery"]


@flask_app.cli.command()
def test():
    #import unittest
    #tests = unittest.TestLoader().discover('tests')
    #unittest.TextTestRunner(verbosity=2).run(tests)
    import pytest
    pytest.main(['tests', '-v'])