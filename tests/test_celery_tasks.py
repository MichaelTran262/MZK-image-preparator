import pytest
from unittest.mock import patch
from krom_app import celery_app
import os

from app.preparator.Preparator import convert_image

class TestCelery:

    def test_convert_image_fifty(self):
        pass