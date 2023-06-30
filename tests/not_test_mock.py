import unittest
from unittest.mock import MagicMock, patch
from app.dataMover.DataMover import DataMover
import os
import shutil

class SendFilesOsTest:
    def test_send_files_os(self):
        dataMover = DataMover()
        # Mock the necessary objects and methods
        mock_folder_db = MagicMock()
        mock_folder_db.folder_name = 'test_folder'
        mock_folder_db.folderPath = '/path/to/source/folder'
        mock_process_db = MagicMock()
        mock_process_db.folders = [mock_folder_db]
        mock_db_session = MagicMock()
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()
        mock_os = MagicMock()
        mock_os.path = os.path
        mock_shutil = MagicMock()
        mock_shutil.copy2 = MagicMock()
        with patch('your_module.FolderDb', return_value=mock_folder_db), \
             patch('your_module.ProcessDb', return_value=mock_process_db), \
             patch('your_module.db.session.add', mock_db_session.add), \
             patch('your_module.db.session.commit', mock_db_session.commit), \
             patch('your_module.os', mock_os), \
             patch('your_module.shutil', mock_shutil):
            # Set up the required attributes for the SendFiles instance
            self.send_files.src_path = '/path/to/source'
            self.send_files.dst_path = '/path/to/destination'
            self.send_files.celery_task_id = 'task_id'
            # Call the method to test
            self.send_files.send_files_os()
            # Assert that the necessary methods and functions were called
            mock_db_session.add.assert_called_with(mock_folder_db)
            mock_db_session.add.assert_called_with(mock_process_db)
            mock_db_session.commit.assert_called()
            mock_os.makedirs.assert_called()  # Check if os.makedirs was called
            # Check if shutil.copy2 was called for each file in the source directory
            mock_shutil.copy2.assert_called()
    def test_send_files_os_database_exception(self):
        # Mock the necessary objects and methods
        mock_db_session = MagicMock()
        mock_db_session.add = MagicMock()
        mock_db_session.commit = MagicMock()
        with patch('your_module.db.session.add', mock_db_session.add), \
             patch('your_module.db.session.commit', mock_db_session.commit), \
             patch('your_module.current_app.logger.error') as mock_logger:
            # Set up the required attributes for the SendFiles instance
            self.send_files.src_path = '/path/to/source'
            self.send_files.dst_path = '/path/to/destination'
            self.send_files.celery_task_id = 'task_id'
            # Raise an exception to simulate a database error
            mock_db_session.commit.side_effect = Exception('Database error')
            # Call the method to test
            self.send_files.send_files_os()
            # Assert that the logger.error method was called with the expected arguments
            mock_logger.assert_called_with("Problem with dabatase: ", mock.ANY)